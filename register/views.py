from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect
from register.forms import RegisterForm
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.forms import PasswordResetForm
from transactions.models import Wallet
from decimal import Decimal
from django.urls import reverse

from social_django.utils import psa
from transactions.models import WalletTransaction, FundRequest
import plotly.graph_objs as go

@csrf_protect
def register_user(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()

            # Check if a wallet already exists for this user
            try:
                wallet = Wallet.objects.get(user=user)
                # Update the wallet's currency and balance if it already exists
                wallet.currency = form.cleaned_data.get("currency")
                if wallet.currency == "GBP":
                    wallet.balance = Decimal("1000.00")
                elif wallet.currency == "USD":
                    wallet.balance = Wallet.currency_converter(Decimal("1000.00"), "GBP", "USD")
                else:
                    wallet.balance = Wallet.currency_converter(Decimal("1000.00"), "GBP", "EUR")
                wallet.save()
            except Wallet.DoesNotExist:
                # Create a new wallet if it doesn't exist yet
                currency = form.cleaned_data.get("currency")
                if currency == "GBP":
                    initial_balance = Decimal("1000.00")
                elif currency == "USD":
                    initial_balance = Wallet.currency_converter(Decimal("1000.00"), "GBP", "USD")
                else:
                    initial_balance = Wallet.currency_converter(Decimal("1000.00"), "GBP", "EUR")
                Wallet.objects.create(user=user, balance=initial_balance, currency=currency)

            # Specify the authentication backend when logging in the user
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')

            messages.success(request, "Registration successful.")
            return redirect("login")
        else:
            messages.error(request, "Unsuccessful registration. Invalid information.")
    else:
        form = RegisterForm()
    return render(request, "register/register.html", {"register_user": form})


@csrf_protect
def login_user(request):
    if request.method == "POST":
        form = AuthenticationForm(request, request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.info(request, f"You are now logged in as {username}.")
                if user.is_staff:
                    admin_url = reverse('admin:index')
                    return redirect(admin_url)
                else:
                    # Get the current user
                    current_user = request.user

                    # Fetch user-specific data for transactions (modify this part based on your data model)
                    pending_transactions = FundRequest.objects.filter(status='PENDING', fund_sender=current_user).count()
                    # receipt_transactions = WalletTransaction.objects.filter(transaction_type='CR', sender=current_user).count()
                    fund_transfer_transactions = WalletTransaction.objects.filter(transaction_type='DR', sender=current_user).count()

                    # Create a bar chart
                    trace = go.Bar(
                        x=['Pending Transactions', 'Fund Transfer Transactions'],
                        y=[pending_transactions, fund_transfer_transactions],
                    )
                    data = [trace]
                    layout = go.Layout(title='Transaction Summary')

                    fig = go.Figure(data=data, layout=layout)

                    # Convert the figure to HTML and pass it to the template
                    plot_html = fig.to_html(full_html=False)

                    # Set a variable to control the navbar display
                    display_navbar = True
                    return render(request, "payapp/dashboard.html", {'plot_html': plot_html, 'display_navbar': display_navbar})
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    return render(request, "register/login.html", {"login_user": form, "facebook_app_id": "your-facebook-app-id"})

def logout_user(request):
    logout(request)
    messages.info(request, "You have successfully logged out.")
    return redirect("home")


def password_reset(request):
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Password reset email sent.')
            return redirect('login')  # replace 'login' with the name of your login view
        else:
            messages.error(request, 'Invalid email.')
    else:
        form = PasswordResetForm()
    return render(request, 'register/password_reset.html', {'form': form})


def password_reset_confirm(request):
    password_reset_confirm(request)
    messages.info(request, "Your password has been reset. You may now log in with your new password.")
    return redirect("login")

@psa('social:complete')
def facebook_callback(request):
    # This view will handle the Facebook authentication callback

    # Retrieve the user's information from the access token
    user = request.backend.do_auth(request.GET.get('access_token'))

    # If the user was authenticated successfully, log them in and redirect to the dashboard
    if user:
        login(request, user)
        messages.success(request, "You have been logged in with Facebook.")
        return redirect('dashboard')

    # If the authentication failed, display an error message
    messages.error(request, "Failed to authenticate with Facebook.")
    return redirect('login')
