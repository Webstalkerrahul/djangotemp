from django.contrib import admin
from .models import Company, BankDetail

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone_number', 'created_at', 'updated_at')
    search_fields = ('name', 'email')
    list_filter = ('created_at',)

@admin.register(BankDetail)
class BankDetailAdmin(admin.ModelAdmin):
    list_display = ('company', 'bank_name', 'account_number', 'ifsc_code', 'branch', 'account_holder_name', 'created_at')
    search_fields = ('bank_name', 'account_number', 'ifsc_code')
    list_filter = ('created_at',)
    raw_id_fields = ('company',)