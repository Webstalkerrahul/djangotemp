from django.contrib import admin
from .models import Vehicle

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('make', 'model','number', 'created_at')
    search_fields = ('make', 'model', 'number')
    list_filter = ('make',)
