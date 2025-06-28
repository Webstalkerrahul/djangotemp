from vendor.models import Vendor, Plant
from django.db.models import Sum, Value, DecimalField
from django.db.models.functions import Coalesce

def get_vendor_data(request):
    """
    Get vendor data for the current user.
    Note: This now returns a QuerySet instead of executing count() here
    to allow pagination to work efficiently.
    """
    vendor_data = Vendor.objects.filter(user=request.user).order_by('-created_at')
    vendor_count = vendor_data.count()
    return vendor_data, vendor_count

def get_plants_data(request):
    """
    Get vendor data for the current user.
    Note: This now returns a QuerySet instead of executing count() here
    to allow pagination to work efficiently.
    """
    plant_data = Plant.objects.filter(user=request.user).order_by('-created_at')
    plant_count = plant_data.count()
    return plant_data, plant_count