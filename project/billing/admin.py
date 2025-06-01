from django.contrib import admin
from .models import Billing, Invoice, GST

@admin.register(Billing)
class BillingAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'rate', 'quantity', 'date','chalan_number', 'created_at')
    search_fields = ('invoice_number',)
    list_filter = ('date',)

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'rate', 'quantity', 'date', 'chalan_number', 'total_amount', 'cgst', 'sgst', 'net_amount', 'amount_in_words', 'created_at')
    search_fields = ('invoice_number',)  # Removed problematic fields
    list_filter = ('date',)  # Removed problematic fields

@admin.register(GST)
class GSTAdmin(admin.ModelAdmin):
    list_display = ('cgst', 'sgst', 'total_gst')
    search_fields = ('cgst', 'sgst', 'total_gst')