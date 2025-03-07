from django.contrib import admin
from .models import Product

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'hsn_code', 'price', 'created_at', 'updated_at')
    search_fields = ('name', 'hsn_code')
    list_filter = ('created_at',)
