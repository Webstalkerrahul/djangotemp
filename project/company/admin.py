from django.contrib import admin
from .models import Company

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone_number', 'created_at', 'updated_at')
    search_fields = ('name', 'email')
    list_filter = ('created_at',)
