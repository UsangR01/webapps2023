from django.db import transaction, OperationalError
from django.db.transaction import on_commit
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from . import models
from .forms import CashTransferForm
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required

from django.http import HttpResponseRedirect
from django.urls import reverse
from django.conf import settings
from decimal import Decimal
from django.db.models import Q

from .models import User, Wallet, WalletTransaction
from django.utils import timezone
from .models import FundRequest
from .forms import FundRequestForm


# Create your views here.
# @transaction.atomic
@login_required
@csrf_protect
def funds_transfer(request):
    src_wallet = None  # Initialize the variable to None
    if request.method == 'POST':
        form = CashTransferForm(request.POST, initial={'sender': request.user.username})  # pass the sender value as initial

        if form.is_valid():
            src_username = form.cleaned_data["sender"]
            dst_username = form.cleaned_data["recipient"]
            amount_to_transfer = form.cleaned_data["amount"]

            # We use the select_for_update inside a transaction block to fetch the queryset to lock it until the transaction is completed.
            src_wallet = models.Wallet.objects.select_related().get(user__username=src_username)
            dst_wallet = models.Wallet.objects.select_related().get(user__username=dst_username)

            if not request.user.is_superuser and request.user.id != src_wallet.user.id:
                messages.error(request, "You can only transfer funds from your own account.")
                return redirect("funds_transfer")

            # check if the sender has enough funds
            if src_wallet.balance < amount_to_transfer:
                messages.error(request, "Insufficient funds.")
                return redirect("funds_transfer")

            # Calculate exchange rate and transfer amount in destination currency if wallets have different currencies
            if src_wallet.currency != dst_wallet.currency:
                rate = models.Wallet.currency_converter(1, src_wallet.currency, dst_wallet.currency)
                amount_to_transfer_recipient_currency = Decimal(str(rate)) * amount_to_transfer
            else:
                amount_to_transfer_recipient_currency = amount_to_transfer

            try:
                src_transaction = None  # initialize the variable with a default value
                with transaction.atomic():
                    src_wallet.balance -= amount_to_transfer
                    src_wallet.save()

                    dst_wallet.balance += amount_to_transfer_recipient_currency
                    dst_wallet.save()

                    if src_username == request.user.username:
                        transaction_type = 'DR'
                        recipient_transaction_type = 'CR'
                    else:
                        transaction_type = 'CR'
                        recipient_transaction_type = 'DR'

                    # Create and save a new WalletTransaction object for the sender
                    src_transaction = WalletTransaction.objects.create(
                        sender=src_username,
                        recipient=dst_username,
                        amount=amount_to_transfer,
                        transaction_type=transaction_type,
                    )

                    # # Create and save a new WalletTransaction object for the recipient
                    # dst_transaction = WalletTransaction.objects.create(
                    #     sender=src_username,
                    #     recipient=dst_username,
                    #     amount=amount_to_transfer_recipient_currency,
                    #     transaction_type=recipient_transaction_type,
                    # )

                # Use the on_commit() function to inform users that all points have been transferred successfully
                @on_commit
                def send_transfer_message():
                    messages.success(request, f"{amount_to_transfer} {src_wallet.currency} have been transferred from {src_username} to {dst_username} .")

            except OperationalError:
                messages.info(request, f"Transfer operation is not possible now.")

        # Fetch all transactions for the source wallet
        src_transactions = list(WalletTransaction.objects.filter(sender=request.user.username).order_by("-date_created"))

        # Fetch all transactions for the destination wallet
        dst_transactions = list(WalletTransaction.objects.filter(recipient=request.user.username).order_by("-date_created"))

        # Render a template showing transaction details
        return render(request, "transactions/account_details.html", {
            "src_wallet": src_wallet,
            "src_transactions": src_transactions,
            "src_transaction_amount": src_transaction.amount,
            "src_transaction_date": src_transaction.date_created,
            "src_transaction_type": src_transaction.transaction_type,
            "src_sender_balance": src_wallet.balance,
            "dst_transactions": dst_transactions,
            "dst_username": dst_username,
        })


    # Set the sender field of the form to the username of the logged-in user
    else:
        form = CashTransferForm(initial={'sender': request.user.username})
    return render(request, "transactions/funds_transfer.html", {"form": form})

@login_required
def transaction_history(request):
    # Fetch all transactions for the source wallet
    src_transactions = list(WalletTransaction.objects.filter(sender=request.user.username, recipient__isnull=False).order_by("-date_created"))

    # Fetch all transactions for the destination wallet
    dst_transactions = list(WalletTransaction.objects.filter(recipient=request.user.username).order_by("-date_created"))

    # Fetch all fund requests sent by the user
    fund_requests_sent = list(FundRequest.objects.filter(fund_sender=request.user).order_by("-created_at"))

    # Fetch all fund requests received by the user excluding ones they sent
    fund_requests_received = list(FundRequest.objects.filter(fund_requester=request.user).exclude(Q(fund_sender=request.user) | Q(fund_sender=None)).order_by("-created_at"))

    # Merge transactions and fund requests into a single list and sort them by date_created or created_at in descending order
    transactions = sorted(
        src_transactions + dst_transactions + fund_requests_sent + fund_requests_received,
        key=lambda x: x.date_created if hasattr(x, 'date_created') else x.created_at,
        reverse=True
    )

    rate = {'USD': 1.24, 'EUR': 1.13, 'GBP': 1.00}
    context = {
        'transactions': transactions,
        'rate': rate
    }
    return render(request, 'transactions/transaction_history.html', context)

def send_and_request(request):
    return render(request, "payapp/send&request.html")

@login_required
def fund_request(request):
    if request.method == 'POST':
        form = FundRequestForm(request.POST, request=request)
        if form.is_valid():
            fund_request = form.save()
            fund_request.fund_requester = request.user
            # Set the currency to the user's currency from their Wallet
            wallet = Wallet.objects.get(user=request.user)
            fund_request.currency = wallet.currency
            fund_request.save()
            messages.success(request, 'Your fund request has been sent.')
            return redirect('fund_request_list')
    else:
        fund_requester = request.user
        # print(fund_requester) # add this line to check the value of fund_requester
        form = FundRequestForm(initial={'fund_requester': fund_requester})
        form.fields['fund_sender'].queryset = User.objects.exclude(pk=fund_requester.pk)
    return render(request, 'transactions/request_fund.html', {'form': form})


def fund_request_list(request):
    pending_requests = FundRequest.objects.filter(fund_sender=request.user, status='PENDING')
    return render(request, 'transactions/fund_request_list.html', {'pending_requests': pending_requests})

def fund_request_action(request, pk):
    request_obj = get_object_or_404(FundRequest, pk=pk)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'approve':
            request_obj.approve()
            messages.success(request, 'The fund request has been approved.')
            #notify = f"Your Fund request of{request_obj.amount}{request_obj.currency} was approved by{request_obj.fund_sender}"
            #Notification.send_notification(fund_requester, notify)
        elif action == 'decline':
            request_obj.decline()
            messages.error(request, 'The fund request has been declined.')
        return redirect('fund_request_list')

    return render(request, 'transactions/fund_request_action.html', {'request': request_obj})

