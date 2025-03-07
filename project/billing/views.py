from django.shortcuts import render
from .models import Billing

def invoice_view(request):
    # You can add context data here if needed
    bills = Billing.objects.order_by('-created_at').first()
    print(bills.rate, bills.quantity)
    return render(request, 'billing.html')

def payment_view(request):
    # You can add context data here if needed
    context = {}
    return render(request, 'billing/payment.html', context)
