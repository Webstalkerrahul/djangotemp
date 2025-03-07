from django.contrib import admin
from .models import Vendor, Plant

@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'is_active', 'vendor_code', 'created_at')
    search_fields = ('name', 'email', 'vendor_code')
    list_filter = ('is_active',)

@admin.register(Plant)
class PlantAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'vendor', 'created_at')
    search_fields = ('name', 'email')
    list_filter = ('vendor',)
