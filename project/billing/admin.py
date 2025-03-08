from django.contrib import admin
from .models import Billing, Invoice

@admin.register(Billing)
class BillingAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'rate', 'quantity', 'date', 'vendor', 'plant', 'product', 'chalan_number', 'company', 'created_at')
    search_fields = ('invoice_number', 'vendor__name', 'product__name')
    list_filter = ('date', 'vendor', 'plant', 'product')

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'rate', 'quantity', 'date', 'vendor', 'plant', 'product', 'chalan_number', 'company', 'total_amount', 'cgst', 'sgst', 'net_amount', 'amount_in_words', 'created_at')
    search_fields = ('invoice_number', 'vendor__name', 'product_name')
    list_filter = ('date', 'vendor', 'plant', 'product')

