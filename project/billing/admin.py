from django.contrib import admin
from .models import Billing
from vendor.models import Vendor
from product.models import Product
from company.models import Company

@admin.register(Billing)
class BillingAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'rate', 'quantity', 'date', 'vendor', 'plant', 'product', 'company')
    search_fields = ('invoice_number',)
    list_filter = ('date', 'vendor', 'plant', 'product', 'company')
