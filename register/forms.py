from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from transactions.models import Wallet

currency_choice = [("GBP", "GBP"), ("USD", "USD"), ("EUR", "EUR")]

# 4 usages
class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    balance = forms.IntegerField(initial=1000)
    currency = forms.ChoiceField(choices=currency_choice, required=True)

    class Meta:
        model = User
        fields = ("username", "balance", "email", "password1", "password2", "currency")

    def save(self, *args, **kwargs):
        instance = super(RegisterForm, self).save(*args, **kwargs)
        Wallet.objects.create(user=instance, balance=self.cleaned_data['balance'])
        return instance

