from django.http import HttpResponse
from datetime import datetime

from django.shortcuts import render
from django.views.decorators.csrf import csrf_protect

from django.shortcuts import render
import plotly.graph_objs as go
from django.contrib.auth.decorators import login_required
from transactions.models import WalletTransaction, FundRequest

import plotly.express as px
import plotly.offline as opy


# Create your views here.
@csrf_protect
def home(request):
    return render(request, "payapp/home.html")

@login_required
def summary(request):
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
    return render(request, 'payapp/dashboard.html', {'plot_html': plot_html, 'display_navbar': display_navbar})

def help(request):
    return render(request, "payapp/help.html")

def contact(request):
    return render(request, "payapp/contact.html")


@login_required
def generate_plot(request):
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
        # x=['Pending Transactions', 'Receipt Transactions', 'Fund Transfer Transactions'],
        # y=[pending_transactions, receipt_transactions, fund_transfer_transactions],
    )
    data = [trace]
    layout = go.Layout(title='Transaction Summary')

    fig = go.Figure(data=data, layout=layout)

    # Convert the figure to HTML and pass it to the template
    plot_html = fig.to_html(full_html=False)

    # Set a variable to control the navbar display
    display_navbar = True
    return render(request, 'payapp/plot_template.html', {'plot_html': plot_html, 'display_navbar': display_navbar})