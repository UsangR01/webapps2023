"""
transactions/urls.py
"""

from django.urls import path
from . import views

urlpatterns = [
    path('fundstransfer/', views.funds_transfer, name='funds_transfer'),
    path('request_funds/', views.fund_request, name='request_funds'),
    path('transactionhistory/', views.transaction_history, name='transaction_history'),
    path('fund_request_list/', views.fund_request_list, name='fund_request_list'),
    path('request/<int:pk>/action/', views.fund_request_action, name='fund_request_action'),
    # path('approve_funds/<int:transaction_id>/', views.approve_funds, name='approve_funds'),
    path('send&request/', views.send_and_request, name="send&request"),
]
