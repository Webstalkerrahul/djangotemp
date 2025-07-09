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
from django.shortcuts import render, get_object_or_404
from core.utils.sql import vendor_helper
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Vendor, Plant
import json
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib import messages 
from django.views.decorators.http import require_http_methods

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
        messages.success(request, "Vendor created successfully!")
        return redirect("vendor:display_vendors")
    
    print("Add vendor page accessed")
    return render(request, "add_vendor.html")

@csrf_exempt
@login_required
def edit_vendor(request, vendor_id):
    """
    Edit an existing vendor - GET shows the form, POST updates the vendor.
    """
    vendor = get_object_or_404(Vendor, id=vendor_id, user=request.user)
    
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
            return render(request, "edit_vendor.html", {
                "vendor": vendor,
                "error": "Name, address, and GST number are required."
            })

        # Update vendor with all provided data
        vendor.name = name
        vendor.email = email if email else None
        vendor.phone = phone if phone else ""
        vendor.address = address
        vendor.vendor_code = vendor_code if vendor_code else None
        vendor.gst_number = gst_number
        vendor.pincode = pincode if pincode else None
        vendor.is_active = is_active
        vendor.save()
        
        messages.success(request, f"Vendor '{vendor.name}' updated successfully!")
        return redirect("vendor:display_vendors")
    
    # GET request - show the form with current vendor data
    return render(request, "edit_vendor.html", {"vendor": vendor})

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def delete_vendor(request, vendor_id):
    """
    Delete a vendor (POST only for security).
    """
    vendor = Vendor.objects.filter(id=vendor_id, user=request.user).first()
    vendor_name = vendor.name
    print(f"Attempting to delete vendor: {vendor_name}")
    
    # Check if vendor has associated plants
    # associated_plants = Plant.objects.filter(vendor=vendor).count()
    # if associated_plants > 0:
    #     messages.error(request, f"Cannot delete vendor '{vendor_name}' because it has {associated_plants} associated plant(s). Please remove or reassign the plants first.")
    #     return redirect("vendor:display_vendors")
    
    vendor.delete()
    messages.success(request, f"Vendor '{vendor_name}' deleted successfully!")
    return redirect("vendor:display_vendors")

@csrf_exempt
@login_required
def edit_plant(request, plant_id):
    """
    Edit an existing plant - GET shows the form, POST updates the plant.
    """
    plant = get_object_or_404(Plant, id=plant_id, user=request.user)
    
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        vendor_id = request.POST.get("vendor")
        email = request.POST.get("email", "").strip()
        phone = request.POST.get("phone", "").strip()
        address = request.POST.get("address", "").strip()
        is_active = request.POST.get("is_active") == "on"
        
        # Validation
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
                vendor = None
        
        if errors:
            vendors = Vendor.objects.filter(user=request.user)
            return render(request, "edit_plant.html", {
                "plant": plant,
                "vendors": vendors,
                "error": " ".join(errors)
            })

        # Update plant with all provided data
        plant.name = name
        plant.vendor = vendor
        plant.email = email if email else None
        plant.phone = phone
        plant.address = address
        plant.is_active = is_active
        plant.save()
        
        messages.success(request, f"Plant '{plant.name}' updated successfully!")
        return redirect("vendor:display_plants")
    
    # GET request - show the form with current plant data
    vendors = Vendor.objects.filter(user=request.user)
    return render(request, "edit_plant.html", {"plant": plant, "vendors": vendors})


@csrf_exempt
@login_required
@require_http_methods(["POST"])
def delete_plant(request, plant_id):
    """
    Delete a plant (POST only for security).
    """
    plant = get_object_or_404(Plant, id=plant_id, user=request.user)
    plant_name = plant.name
    
    plant.delete()
    messages.success(request, f"Plant '{plant_name}' deleted successfully!")
    return redirect("vendor:display_plants")