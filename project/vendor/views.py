from django.shortcuts import render
from core.utils.sql import vendor_helper
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Vendor, Plant
import json
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib import messages 

# Create your views here.
def display_vendors(request):
    """
    Render the home page with paginated vendors.
    """
    vendor_data, vendor_count = vendor_helper.get_vendor_data(request)
    
    # Get the page number from request
    page_number = request.GET.get('page', 1)
    
    # Create paginator (10 vendors per page, you can adjust this number)
    paginator = Paginator(vendor_data, 10)
    
    try:
        vendors_page = paginator.page(page_number)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page
        vendors_page = paginator.page(1)
    except EmptyPage:
        # If page is out of range, deliver last page
        vendors_page = paginator.page(paginator.num_pages)
    
    context = {
        'vendors': vendors_page,  # This is the paginated page object
        'vendor_count': vendor_count,
    }
    
    return render(request, "vendor_display.html", context)


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

def display_plants(request):
    """
    Render the home page with paginated plants.
    """
    plant_data, plant_count = vendor_helper.get_plants_data(request)

    # Get the page number from request
    page_number = request.GET.get('page', 1)

    # Create paginator (10 plants per page, you can adjust this number)
    paginator = Paginator(plant_data, 10)

    
    try:
        plants_page = paginator.page(page_number)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page
        plants_page = paginator.page(1)
    except EmptyPage:
        # If page is out of range, deliver last page
        plants_page = paginator.page(paginator.num_pages)

    context = {
        'plants': plants_page,  # This is the paginated page object
        'plant_count': plant_count,
    }

    return render(request, "plant_display.html", context)


def add_plant_manual(request):
    """
    Handle the “Add Plant” form – GET shows the form,
    POST validates input and creates a Plant linked to the chosen Vendor.
    """
    if request.method == "POST":
        # ----- fetch & tidy incoming data -----------------------------------
        name       = request.POST.get("name", "").strip()
        vendor_id  = request.POST.get("vendor")            # comes from <select>
        email      = request.POST.get("email", "").strip()
        phone      = request.POST.get("phone", "").strip()
        address    = request.POST.get("address", "").strip()
        is_active  = request.POST.get("is_active") == "on"  # checkbox (optional)

        # ----- validation ----------------------------------------------------
        errors = []
        if not name:
            errors.append("Plant name is required.")
        if not vendor_id:
            errors.append("Please choose an associated vendor.")
        else:
            # confirm the vendor really belongs to the logged‑in user
            try:
                vendor = Vendor.objects.get(id=vendor_id, user=request.user)
            except Vendor.DoesNotExist:
                errors.append("Selected vendor was not found.")
                vendor = None  # keep variable defined

        if errors:
            # show the form again with error(s) and keep the vendors list
            vendors = Vendor.objects.filter(user=request.user)
            return render(
                request,
                "add_plant.html",
                {"error": " ".join(errors), "vendors": vendors},
            )

        Plant.objects.create(
            name=name,
            vendor=vendor,
            email=email or None,
            phone=phone,
            address=address,
            user=request.user,
        )

        messages.success(request, "Plant created successfully!")
        return redirect("vendor:display_plants")  # go to your listing page

    # ----- GET: show blank form ---------------------------------------------
    vendors = Vendor.objects.filter(user=request.user)
    return render(request, "add_plant.html", {"vendors": vendors})