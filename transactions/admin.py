from django.contrib import admin

from .models import Wallet
from .models import WalletTransaction
from .models import FundRequest
# Register your models here.

admin.site.register(Wallet)
admin.site.register(WalletTransaction)
admin.site.register(FundRequest)
