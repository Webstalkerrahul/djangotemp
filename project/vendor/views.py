from django.shortcuts import render
from core.utils.sql import vendor_helper
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Vendor
import json
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required

# Create your views here.
def display_vendors(request):
    """
    Render the home page.
    """
    vendor_data, vendor_count = vendor_helper.get_vendor_data(request)
    context = {
        'vendors': vendor_data,
        'vendor_count': vendor_count
    }

    return render(request, "vendor_display.html", context)  # Adjust the template name as needed


def add_vendor_manual(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip()
        phone = request.POST.get("phone", "").strip()
        address = request.POST.get("address", "").strip()
        vendor_code = request.POST.get("vendor_code", "").strip()
        gst_number = request.POST.get("gst_number", "").strip()
        pincode = request.POST.get("pincode", "").strip()
        is_active = request.POST.get("is_active") == "on"
        
        # Validation - only name, address, and GST number are required
        if not name or not address or not gst_number:
            return render(request, "add_vendor.html", {
                "error": "Name, address, and GST number are required."
            })

        # Create vendor with all provided data
        Vendor.objects.create(
            name=name,
            email=email if email else None,
            phone=phone if phone else "",
            address=address,
            vendor_code=vendor_code if vendor_code else None,
            gst_number=gst_number,
            pincode=pincode if pincode else None,
            is_active=is_active,
            user=request.user
        )
        return redirect("vendor:display_vendors")
    
    print("Add vendor page accessed")
    return render(request, "add_vendor.html")