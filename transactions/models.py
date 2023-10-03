from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import requests
from decimal import Decimal
from django.db import transaction
from notifications.models import Notification


# Create your models here.
class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="balance")
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=1000)
    currency = models.CharField(max_length=3, default='GBP')
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        details = ''
        details += f'Username           :{self.user}\n'
        details += f'Account Balance    :{self.balance}\n'
        details += f'Currency           :{self.currency}\n'
        return details

    @staticmethod
    def currency_converter(points, base_currency, quote_currency):
        url = "https://api.exchangerate-api.com/v4/latest/{}".format(base_currency)
        response = requests.get(url)
        raw_data = response.json()
        rates = raw_data["rates"]
        rate = rates.get(quote_currency)
        if rate:
            rate = Decimal(str(rate))
            points = Decimal(str(points))
            return round(points * rate, 2)

class WalletTransaction(models.Model):
    TRANSACTION_TYPE_CHOICES = [
        ('CR', 'Credit'),
        ('DR', 'Debit'),
    ]
    sender = models.CharField(max_length=50, null=False)
    recipient = models.CharField(max_length=50, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=2, choices=TRANSACTION_TYPE_CHOICES, default='CR')
    date_created = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.sender} - {self.recipient}: {self.amount}"


class FundRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('DECLINED', 'Declined'),
    ]
    fund_requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='fund_requests', null=False)
    fund_sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_fund_requests')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.CharField(max_length=500)
    currency = models.CharField(max_length=3, default='GBP')
    approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    approved_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')

    def __str__(self):
        return f'{self.fund_requester.username} - {self.fund_sender.username} - {self.amount} {self.currency}'

    @transaction.atomic
    def approve(self):
        self.status = 'APPROVED'
        self.created_at = timezone.now()
        self.approved = True

        # Get the wallets of the requester and sender
        requester_wallet = Wallet.objects.get(user=self.fund_requester)
        sender_wallet = Wallet.objects.get(user=self.fund_sender)

        # Convert the requested amount to the sender's currency
        converted_amount = requester_wallet.currency_converter(self.amount, self.currency, sender_wallet.currency)

        with transaction.atomic():
            # Update the fund_sender wallet balance
            sender_wallet.balance -= Decimal(converted_amount)
            sender_wallet.save()

            # Update the balances of the requester and sender
            requester_wallet.balance += Decimal(self.amount)
            requester_wallet.save()

            self.save()

            # Create a notification for the requester
            recipient = self.fund_requester
            alert = f"Your fund request for {self.amount} {self.currency} has been approved."
            Notification.objects.create(recipient=recipient, message=alert)

    def decline(self):
        self.status = 'DECLINED'
        self.created_at = timezone.now()
        self.save()

        # Create a notification for the requester
        recipient = self.fund_requester
        alert = f"Your fund request for {self.amount} {self.currency} has been declined."
        Notification.objects.create(recipient=recipient, message=alert)

    class Meta:
        ordering = ['-created_at']

