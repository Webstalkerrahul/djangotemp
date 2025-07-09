from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.template.loader import render_to_string
from playwright.sync_api import sync_playwright
import tempfile
import os
import base64
from django.conf import settings
from core.utils import queries
from datetime import datetime
from django.contrib.auth.decorators import login_required
from twilio.rest import Client
from django.core.cache import cache
from django.conf import settings
import json
from django.views.decorators.csrf import csrf_exempt, csrf_protect   
from core.utils.sql import invoice_helper
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import Invoice, Vendor, Company, Plant, Vehicle, Product, Billing
from django.views.decorators.http import require_POST
from django.http import HttpResponseServerError
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone
from datetime import datetime, timedelta

@login_required
@csrf_exempt
def generate_invoice(request):
    """Optimized invoice generation endpoint"""
    if request.method == 'POST':
        try:
            # Process input data
            invoice_number = request.POST.get('invoice_number')
            vendor_id = request.POST.get('vendor')
            line_items_json = request.POST.get('line_items')
            
            if not line_items_json:
                return JsonResponse({'error': 'No line items provided'}, status=400)
            
            line_items = json.loads(line_items_json)
            
            
            # DEBUG: Check each line item for required fields
           
            gst_rate = request.POST.get('gst_rate', '12')
            
            # Validate line items before processing
            validated_line_items = []
            for i, item in enumerate(line_items):
                # Check if product information exists
                product_id = item.get('product_id') or item.get('product')
                if not product_id:
                    return JsonResponse({
                        'error': f'Line item {i+1} is missing product information'
                    }, status=400)
                
                # Verify product exists in database
                try:
                    from product.models import Product  # Replace with your actual import
                    product = Product.objects.get(id=product_id)
                    item['product_id'] = product.id
                    item['product'] = product.id  # Ensure both fields are set
                except Product.DoesNotExist:
                    return JsonResponse({
                        'error': f'Product with ID {product_id} does not exist'
                    }, status=400)
                
                validated_line_items.append(item)
            
            # Create invoice in transaction
            invoice = queries.add_multi_line_invoice(
                request.user,
                invoice_number, 
                vendor_id, 
                validated_line_items,  # Use validated items
                gst_rate=gst_rate,
                bank_detail=request.POST.get('bank_detail'),
            )
            
            if not invoice:
                return JsonResponse({'error': 'Invoice creation failed'}, status=500)
            
            # DEBUG: Check if billing items were created
            billing_items_count = Billing.objects.filter(invoice_number=invoice.invoice_number).count()
            
            # Generate PDF with optimized function
            flag = request.user.username == 'sahil'
            return render_invoice_pdf(invoice, flag, gst_rate)
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format for line_items'}, status=400)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({'error': str(e)}, status=500)
    
 # GET request - optimized data fetching
    try:
        context = {
            'vendors': queries.get_vendor(request.user),
            'products': queries.get_product(request.user),
            'company': queries.get_company(request.user).first(),
            'plants': queries.get_plant(request.user),
            'vehicles': queries.get_vehicle(request.user),
            'gst': queries.get_gst(),
            'username': request.user.username,
            'bank_details': queries.get_bank_details(request.user),
        }
        return render(request, 'billing.html', context)
    except Exception as e:
        return HttpResponseServerError("Error loading page")
@csrf_exempt
def render_invoice_pdf(invoice, flag, gst_rate):
    try:
        # Decide quote & logo file **before** cache lookup
        is_rushika = "rushika" in str(invoice.company.name).lower()
        top_quote  = "Jai ShreeKrishna" if is_rushika else "SHREE GANESHAY NAMAH"
        logo_file  = "rushika_logo.png"  if is_rushika else "logo.png"

        # Cache the logo image as data URL
        cache_key = f"logo_{invoice.company.id}_{logo_file}"
        logo_data_url = cache.get(cache_key)
        if not logo_data_url:
            logo_path = os.path.join(settings.BASE_DIR, 'billing/static', logo_file)
            with open(logo_path, "rb") as image_file:
                encoded_logo = base64.b64encode(image_file.read()).decode("utf-8")
            logo_data_url = f"data:image/png;base64,{encoded_logo}"
            cache.set(cache_key, logo_data_url, 3600)

        # Get billing items (line items) for this invoice with proper relationships
        billing_items = Billing.objects.filter(
            invoice_number=invoice.invoice_number
        ).select_related('vendor', 'plant', 'product', 'vehicle', 'company').order_by('id')
        
        
        # If no billing items found, try to create a single item from the invoice itself
        if not billing_items.exists():
            quantity = float(invoice.quantity) if invoice.quantity else 0.0
            rate = float(invoice.rate) if invoice.rate else 0.0
            amount = quantity * rate
            
            invoice_items = [{
                'date': invoice.date,
                'chalan_number': getattr(invoice, 'chalan_number', ''),
                'vehicle': invoice.vehicle,
                'product': invoice.product,
                'plant': invoice.plant,
                'vendor': invoice.vendor,
                'quantity': quantity,
                'rate': rate,
                'amount': amount,
                'hsn_code': getattr(invoice.product, 'hsn_code', '') if invoice.product else '',
            }]
        else:
            # Calculate amount for each item (since it might not be stored)
            invoice_items = []
            for item in billing_items:
                quantity = float(item.quantity) if item.quantity else 0.0
                rate = float(item.rate) if item.rate else 0.0
                amount = quantity * rate
                
                item_dict = {
                    'date': item.date,
                    'chalan_number': item.chalan_number,
                    'vehicle': item.vehicle,
                    'product': item.product,
                    'plant': item.plant,
                    'vendor': item.vendor,
                    'quantity': quantity,
                    'rate': rate,
                    'amount': amount,
                    'hsn_code': getattr(item.product, 'hsn_code', '') if item.product else '',
                }
                invoice_items.append(item_dict)

        # Calculate totals with proper numeric conversion
        subtotal = sum(float(item['amount']) for item in invoice_items)
        gst_rate_float = float(gst_rate) if gst_rate else 0.0
        cgst_amount = subtotal * (gst_rate_float / 2 / 100)
        sgst_amount = subtotal * (gst_rate_float / 2 / 100)
        total_amount = subtotal + cgst_amount + sgst_amount

        # UPDATE: Set the calculated values on the invoice object
        invoice.total_amount = subtotal
        invoice.cgst = cgst_amount
        invoice.sgst = sgst_amount
        invoice.net_amount = total_amount
        
        # Convert amount to words
        from core.utils.amount_to_words import num_to_words_indian
        invoice.amount_in_words = num_to_words_indian(int(total_amount))
        
        # Get bank details - FIX: Get from user's bank details
        try:
            # Try to get bank details from the user or company
            bank_details = queries.get_bank_details(invoice.vendor.user if hasattr(invoice.vendor, 'user') else None)
            if bank_details.exists():
                invoice.bank_details = bank_details.first()
            else:
                # Fallback: create a default bank details object
                from types import SimpleNamespace
                invoice.bank_details = SimpleNamespace(
                    bank_name="Not Available",
                    account_holder_name="Not Available", 
                    account_number="Not Available",
                    ifsc_code="Not Available",
                    branch="Not Available"
                )
        except Exception as e:
            # Create default bank details
            from types import SimpleNamespace
            invoice.bank_details = SimpleNamespace(
                bank_name="Not Available",
                account_holder_name="Not Available", 
                account_number="Not Available",
                ifsc_code="Not Available",
                branch="Not Available"
            )

        # Build context for HTML rendering
        context = {
            "invoice": invoice,
            "logo_data_url": logo_data_url,
            "cgst_rate": float(gst_rate) / 2,
            "sgst_rate": float(gst_rate) / 2,
            "total_gst_rate": gst_rate,
            "top_quote": top_quote,
            "invoice_items": invoice_items,
            "subtotal": subtotal,
            "cgst_amount": cgst_amount,
            "sgst_amount": sgst_amount,
            "total_amount": total_amount,
            "items_count": len(invoice_items),
        }

        # Render template and generate PDF using Playwright
        template_name = "demo_template.html" if flag else "bill_template.html"
        html_content = render_to_string(template_name, context)


        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=['--disable-dev-shm-usage', '--no-sandbox', '--disable-setuid-sandbox']
            )
            page = browser.new_page()
            
            # Increase timeout and disable waiting for resources
            page.set_default_timeout(30000)  # 30 seconds instead of 5
            
            # Method 1: Use set_content with wait_until='domcontentloaded'
            try:
                page.set_content(html_content, wait_until='domcontentloaded')
            except Exception as content_error:
                # Method 2: Alternative approach using goto with data URL
                data_url = f"data:text/html;charset=utf-8,{html_content}"
                page.goto(data_url, wait_until='domcontentloaded')
            
            # Wait for any additional resources to load (optional)
            try:
                page.wait_for_load_state("networkidle", timeout=10000)  # 10 seconds max
            except:
                # If networkidle fails, just wait for domcontentloaded
                page.wait_for_load_state("domcontentloaded", timeout=5000)
            
            # Generate PDF
            pdf_data = page.pdf(
                format="A4",
                print_background=True,
                margin={"top": "0mm", "right": "0mm", "bottom": "0mm", "left": "0mm"},
            )
            browser.close()

        # Save to storage
        pdf_filename = f"invoice-no-{invoice.invoice_number}-{datetime.now():%d-%m-%Y-%H-%M}.pdf"
        pdf_rel_path = f"invoices/{pdf_filename}"
        full_path = default_storage.save(pdf_rel_path, ContentFile(pdf_data))

        # Save PDF file path to the Invoice model
        invoice.pdf.name = full_path
        invoice.save(update_fields=["pdf"])

        # Return PDF response for download (remove the redirect)
        response = HttpResponse(pdf_data, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{pdf_filename}"'  # Changed to 'attachment' for download
        return response  # Return the PDF response instead of redirecting

    except Exception as e:
        import traceback
        traceback.print_exc()
        return HttpResponseServerError("Error generating PDF")

# API endpoint to add line items dynamically
@login_required
def add_invoice_line_item(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['date', 'chalan_number', 'vehicle_id', 'product_id', 'quantity', 'rate']
        for field in required_fields:
            if field not in data:
                return JsonResponse({'error': f'Missing field: {field}'}, status=400)
        
        # Calculate amount
        amount = float(data['quantity']) * float(data['rate'])
        
        line_item = {
            'date': data['date'],
            'chalan_number': data['chalan_number'],
            'vehicle_id': data['vehicle_id'],
            'product_id': data['product_id'],
            'quantity': data['quantity'],
            'rate': data['rate'],
            'amount': amount
        }
        
        return JsonResponse({'success': True, 'line_item': line_item})
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)

def serve_temp_pdf(request, cache_key):
    pdf_data = cache.get(cache_key)
    if pdf_data:
        response = HttpResponse(pdf_data, content_type="application/pdf")
        response["Content-Disposition"] = f'inline; filename="invoice.pdf"'
        return response
    return HttpResponse("PDF not found", status=404)

def home(request):
    print("Home page accessed")
    return render(request, "home.html")

@csrf_exempt 
def view_invoices(request):
    """Enhanced view with complete billing statistics"""
    invoices, total = invoice_helper.get_invoice_data(request)

    paginator = Paginator(invoices, 10)
    page = request.GET.get('page')
    
    try:
        invoices_page = paginator.page(page)
    except PageNotAnInteger:
        invoices_page = paginator.page(1)
    except EmptyPage:
        invoices_page = paginator.page(paginator.num_pages)
    
    # Get comprehensive billing statistics
    billing_stats = get_billing_statistics(request.user)
    
    # Calculate averages and totals
    total_count = paginator.count
    avg_value = total / total_count if total_count > 0 else 0
    
    data = {
        "invoices": invoices_page,
        "request": request,
        "total": total,
        "avg_value": avg_value,
        "billing_stats": billing_stats,
        "total_invoices": total_count,
        "pending_invoices": billing_stats.get('pending_count', 0),
        "paid_invoices": billing_stats.get('paid_count', 0),
        "pending_amount": billing_stats.get('pending_amount', 0),
    }

    return render(request, "invoice_display.html", data)

def get_billing_statistics(user):
    """Get comprehensive billing statistics for dashboard"""
    try:
        # Get current month date range
        now = timezone.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Base queryset for user's invoices
        user_invoices = Invoice.objects.filter(
            Q(created_by=user) | Q(vendor__created_by=user) | Q(company__created_by=user)
        )
        
        # Get all billing entries for user
        user_billing = Billing.objects.filter(
            Q(created_by=user) | Q(vendor__created_by=user) | Q(company__created_by=user)
        )
        
        # Calculate totals
        total_revenue = user_invoices.aggregate(
            total=Sum('net_amount')
        )['total'] or 0
        
        # Calculate this month's revenue
        monthly_revenue = user_invoices.filter(
            created_at__gte=start_of_month
        ).aggregate(
            total=Sum('net_amount')
        )['total'] or 0
        
        # Get invoice counts by status (you may need to add status field to Invoice model)
        # For now, we'll use a simple heuristic: invoices created in last 30 days as "pending"
        # and older ones as "paid" - adjust this logic based on your business rules
        
        thirty_days_ago = now - timedelta(days=30)
        
        pending_invoices = user_invoices.filter(
            created_at__gte=thirty_days_ago
        )
        
        paid_invoices = user_invoices.filter(
            created_at__lt=thirty_days_ago
        )
        
        pending_stats = pending_invoices.aggregate(
            count=Count('id'),
            amount=Sum('net_amount')
        )
        
        paid_stats = paid_invoices.aggregate(
            count=Count('id'),
            amount=Sum('net_amount')
        )
        
        # Average invoice value
        avg_invoice_value = user_invoices.aggregate(
            avg=Avg('net_amount')
        )['avg'] or 0
        
        # Get billing line items statistics
        billing_stats = user_billing.aggregate(
            total_quantity=Sum('quantity'),
            total_billing_amount=Sum('quantity') * Sum('rate') if user_billing.exists() else 0,
            avg_rate=Avg('rate')
        )
        
        # Monthly trends (last 6 months)
        monthly_data = []
        for i in range(6):
            month_start = (now - timedelta(days=30*i)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            
            month_revenue = user_invoices.filter(
                created_at__gte=month_start,
                created_at__lte=month_end
            ).aggregate(
                total=Sum('net_amount'),
                count=Count('id')
            )
            
            monthly_data.append({
                'month': month_start.strftime('%b %Y'),
                'revenue': month_revenue['total'] or 0,
                'count': month_revenue['count'] or 0
            })
        
        return {
            'total_revenue': total_revenue,
            'monthly_revenue': monthly_revenue,
            'pending_count': pending_stats['count'] or 0,
            'pending_amount': pending_stats['amount'] or 0,
            'paid_count': paid_stats['count'] or 0,
            'paid_amount': paid_stats['amount'] or 0,
            'avg_invoice_value': avg_invoice_value,
            'total_quantity': billing_stats['total_quantity'] or 0,
            'avg_rate': billing_stats['avg_rate'] or 0,
            'monthly_trends': monthly_data,
            'total_invoices': user_invoices.count(),
        }
        
    except Exception as e:
        return {
            'total_revenue': 0,
            'monthly_revenue': 0,
            'pending_count': 0,
            'pending_amount': 0,
            'paid_count': 0,
            'paid_amount': 0,
            'avg_invoice_value': 0,
            'total_quantity': 0,
            'avg_rate': 0,
            'monthly_trends': [],
            'total_invoices': 0,
        }


@csrf_exempt 
def edit_invoice(request, invoice_id):
    """
    View to edit an existing invoice with line items
    """
    invoice = get_object_or_404(Invoice, id=invoice_id)
    
    # Get all billing records (line items) for this invoice
    billing_items = Billing.objects.filter(
        invoice_number=invoice.invoice_number
    ).select_related('vendor', 'plant', 'product', 'vehicle', 'company')
    
    if request.method == 'POST':
        try:
            # Update main invoice fields
            invoice.chalan_number = request.POST.get('chalan_number', '')
            
            # Update foreign key relationships if needed
            vendor_id = request.POST.get('vendor')
            if vendor_id:
                invoice.vendor = get_object_or_404(Vendor, id=vendor_id)
            
            company_id = request.POST.get('company')
            if company_id:
                invoice.company = get_object_or_404(Company, id=company_id)
            
            plant_id = request.POST.get('plant')
            if plant_id:
                invoice.plant = get_object_or_404(Plant, id=plant_id)
            
            vehicle_id = request.POST.get('vehicle')
            if vehicle_id:
                invoice.vehicle = get_object_or_404(Vehicle, id=vehicle_id)
            
            product_id = request.POST.get('product')
            if product_id:
                invoice.product = get_object_or_404(Product, id=product_id)
            
            # Update numeric fields
            invoice.quantity = float(request.POST.get('quantity', 0))
            invoice.rate = float(request.POST.get('rate', 0))
            invoice.net_amount = float(request.POST.get('net_amount', 0)) if request.POST.get('net_amount') else None
            invoice.cgst = float(request.POST.get('cgst', 0)) if request.POST.get('cgst') else None
            invoice.sgst = float(request.POST.get('sgst', 0)) if request.POST.get('sgst') else None
            invoice.total_amount = float(request.POST.get('total_amount', 0))
            
            # Update date
            from datetime import datetime
            date_str = request.POST.get('date')
            if date_str:
                invoice.date = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            # Handle line items updates
            line_item_ids = request.POST.getlist('line_item_id[]')
            line_item_chalans = request.POST.getlist('line_item_chalan[]')
            line_item_dates = request.POST.getlist('line_item_date[]')
            line_item_quantities = request.POST.getlist('line_item_quantity[]')
            line_item_rates = request.POST.getlist('line_item_rate[]')
            line_item_vehicles = request.POST.getlist('line_item_vehicle[]')
            line_item_products = request.POST.getlist('line_item_product[]')
            line_item_plants = request.POST.getlist('line_item_plant[]')
            
            # Update existing line items
            for i, item_id in enumerate(line_item_ids):
                if item_id:  # Existing item
                    billing_item = get_object_or_404(Billing, id=item_id)
                    billing_item.chalan_number = line_item_chalans[i]
                    billing_item.date = datetime.strptime(line_item_dates[i], '%Y-%m-%d').date()
                    billing_item.quantity = float(line_item_quantities[i])
                    billing_item.rate = float(line_item_rates[i])
                    
                    if line_item_vehicles[i]:
                        billing_item.vehicle = get_object_or_404(Vehicle, id=line_item_vehicles[i])
                    if line_item_products[i]:
                        billing_item.product = get_object_or_404(Product, id=line_item_products[i])
                    if line_item_plants[i]:
                        billing_item.plant = get_object_or_404(Plant, id=line_item_plants[i])
                    
                    billing_item.save()
                else:  # New item
                    if line_item_chalans[i]:  # Only create if chalan number exists
                        Billing.objects.create(
                            invoice_number=invoice.invoice_number,
                            chalan_number=line_item_chalans[i],
                            date=datetime.strptime(line_item_dates[i], '%Y-%m-%d').date(),
                            quantity=float(line_item_quantities[i]),
                            rate=float(line_item_rates[i]),
                            vehicle_id=line_item_vehicles[i] if line_item_vehicles[i] else None,
                            product_id=line_item_products[i] if line_item_products[i] else None,
                            plant_id=line_item_plants[i] if line_item_plants[i] else None,
                            vendor=invoice.vendor,
                            company=invoice.company,
                        )
            
            # Recalculate totals based on updated line items
            updated_billing_items = Billing.objects.filter(invoice_number=invoice.invoice_number)
            total_amount = sum(item.quantity * item.rate for item in updated_billing_items)
            
            # Update GST calculations
            gst_rate = float(request.POST.get('gst_rate', 12))
            cgst = total_amount * (gst_rate / 2) / 100
            sgst = total_amount * (gst_rate / 2) / 100
            net_amount = total_amount + cgst + sgst
            
            invoice.total_amount = total_amount
            invoice.cgst = cgst
            invoice.sgst = sgst
            invoice.net_amount = net_amount
            
            # Save the updated invoice
            invoice.save()
            
            messages.success(request, f'Invoice #{invoice.invoice_number} has been updated successfully!')
            return redirect('billing:view_invoices')
            
        except Exception as e:
            messages.error(request, f'Error updating invoice: {str(e)}')
    
    # Get all related objects for dropdowns
    context = {
        'invoice': invoice,
        'billing_items': billing_items,
        'vendor': queries.get_vendor(request.user),
        'product': queries.get_product(request.user),
        'company': queries.get_company(request.user),
        'plant': queries.get_plant(request.user),
        'vehicle': queries.get_vehicle(request.user),
        'gst': queries.get_gst(),
        'bank_details': queries.get_bank_details(request.user),
    }
    
    return render(request, 'edit_invoice.html', context)

@csrf_exempt 
@require_POST     
def delete_invoice(request, invoice_id):
    """
    View to delete an invoice
    """
    invoice = get_object_or_404(Invoice, id=invoice_id)
    
    
    if request.method == 'POST':
        try:
            invoice_number = invoice.invoice_number
            invoice.delete()
            messages.success(request, f'Invoice #{invoice_number} has been deleted successfully!')
        except Exception as e:
            messages.error(request, f'Error deleting invoice: {str(e)}')
    else:
        # If GET request, redirect back to invoices list
        messages.warning(request, 'Invalid request method for delete operation.')
    
    return redirect('billing:view_invoices')

@csrf_exempt 
@require_POST
def delete_invoice_ajax(request, invoice_id):
    """
    AJAX view to delete an invoice (optional - for AJAX requests)
    """
    try:
        invoice = get_object_or_404(Invoice, id=invoice_id)
        invoice_number = invoice.invoice_number
        invoice.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Invoice #{invoice_number} has been deleted successfully!'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error deleting invoice: {str(e)}'
        }, status=400)
    
from django.http import FileResponse
import glob

def invoice_pdf_view(request, pk):
    """
    Return the saved PDF for an invoice (or regenerate it on the fly).
    """
    invoice = get_object_or_404(Invoice, pk=pk)

    # 1) Look for an existing PDF file that starts with invoice-no-{number}
    pattern = os.path.join(settings.MEDIA_ROOT, "invoices",
                           f"invoice-no-{invoice.invoice_number}-*.pdf")
    matches = sorted(glob.glob(pattern), reverse=True)  # newest first

    if matches:
        return FileResponse(open(matches[0], "rb"),
                            content_type="application/pdf",
                            filename=os.path.basename(matches[0]),
                            as_attachment=False)      # inline view
    # 2) Fallback: regenerate on the fly
    return render_invoice_pdf(invoice, flag=False, gst_rate=invoice.gst or 12)

@login_required
@require_POST
@csrf_protect
def delete_invoice(request, invoice_id):
    """
    Delete an invoice and its associated PDF file
    """
    try:
        # Get the invoice object or return 404 if not found
        invoice = get_object_or_404(Invoice, id=invoice_id)
        
        # Check if the user has permission to delete this invoice
        # Add your permission logic here if needed
        # For example, if invoices belong to users:
        # if invoice.user != request.user:
        #     messages.error(request, "You don't have permission to delete this invoice.")
        #     return redirect('billing:view_invoices')
        
        # Store invoice number for the success message
        invoice_number = invoice.invoice_number
        
        # Delete the PDF file if it exists
        if invoice.pdf:
            try:
                if os.path.exists(invoice.pdf.path):
                    os.remove(invoice.pdf.path)
            except Exception as e:
                # Log the error but don't fail the deletion
                print(f"Error deleting PDF file: {e}")
        
        # Delete the invoice from the database
        invoice.delete()
        
        # Add success message
        messages.success(request, f'Invoice {invoice_number} has been deleted successfully.')
        
        # Return JSON response for AJAX requests
        if request.headers.get('Content-Type') == 'application/json':
            return JsonResponse({
                'success': True,
                'message': f'Invoice {invoice_number} has been deleted successfully.'
            })
        
        # Redirect to the invoices list page
        return redirect('billing:view_invoices')
        
    except Invoice.DoesNotExist:
        messages.error(request, 'Invoice not found.')
        if request.headers.get('Content-Type') == 'application/json':
            return JsonResponse({
                'success': False,
                'message': 'Invoice not found.'
            }, status=404)
        return redirect('billing:view_invoices')
        
    except Exception as e:
        # Handle any other errors
        messages.error(request, f'An error occurred while deleting the invoice: {str(e)}')
        if request.headers.get('Content-Type') == 'application/json':
            return JsonResponse({
                'success': False,
                'message': f'An error occurred while deleting the invoice: {str(e)}'
            }, status=500)
        return redirect('billing:view_invoices')