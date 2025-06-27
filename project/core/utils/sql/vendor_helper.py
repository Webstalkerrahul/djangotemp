from vendor.models import Vendor
from django.db.models import Sum, Value, DecimalField
from django.db.models.functions import Coalesce

def get_vendor_data(request):
    vendor_data = Vendor.objects.filter(user=request.user).order_by('-created_at')

    vendor_count = vendor_data.count()
    return vendor_data, vendor_count
