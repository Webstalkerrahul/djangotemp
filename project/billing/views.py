
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
from .models import Invoice, Vendor, Company, Plant, Vehicle, Product
from django.views.decorators.http import require_POST

@login_required
@csrf_exempt
def generate_invoice(request):
    if request.method == 'POST':
        # Get basic invoice data
        invoice_number = request.POST.get('invoice_number')
        vendor_id = request.POST.get('vendor')
        company_id = request.POST.get('company')
        # Get line items data (assuming JSON format from frontend)
        line_items_json = request.POST.get('line_items')
        
        if not line_items_json:
            return render(request, 'billing.html', {'error': 'No line items provided'})
        
        try:
            line_items = json.loads(line_items_json)
        except json.JSONDecodeError:
            return render(request, 'billing.html', {'error': 'Invalid line items format'})
        gst_rate = request.POST.get('gst_rate',0)
        # Create invoice with multiple line items
        invoice = queries.add_multi_line_invoice(
            request.user,
            invoice_number, 
            vendor_id, 
            line_items,
            gst_rate = gst_rate,
            bank_detail = request.POST.get('bank_detail', None),
        )
        
        if invoice is None:
            return render(request, 'billing.html', {'error': 'Error creating invoice'})
        else:
            flag = request.user.username == 'sahil'
            response = render_invoice_pdf(invoice, flag, gst_rate)
            return response
    # GET request - show form
    vendor = queries.get_vendor(request.user)
    product = queries.get_product(request.user)
    company = queries.get_company(request.user)
    plant = queries.get_plant(request.user)
    vehicle = queries.get_vehicle(request.user)
    gst = queries.get_gst()
    bank_details =  queries.get_bank_details(request.user)
    
    return render(request, 'billing.html', {
        'vendors': vendor, 
        'products': product, 
        'company': company, 
        'plants': plant, 
        'vehicles': vehicle,
        'gst': gst,
        "username":request.user.username,
        'bank_details': bank_details
    })

@csrf_exempt
def render_invoice_pdf(invoice, flag, gst_rate):
    date_obj = datetime.now()
    formatted_datetime = date_obj.strftime("%d-%m-%Y-%H-%M")
    if "rushika" in str(invoice.company.name).lower():
        logo_path = os.path.join(settings.BASE_DIR, 'billing/static', 'rushika_logo.png')
        top_quote = "Jai ShreeKrishna"
    else:
        logo_path = os.path.join(settings.BASE_DIR, 'billing/static', 'logo.png')
        top_quote = "SHREE GANESHAY NAMAH"
    
    with open(logo_path, "rb") as image_file:
        encoded_logo = base64.b64encode(image_file.read()).decode('utf-8')
    
    logo_data_url = f"data:image/png;base64,{encoded_logo}"
    context = {
        "invoice": invoice,
        "logo_data_url": logo_data_url,
        "cgst_rate": float(gst_rate)/2,
        "sgst_rate":  float(gst_rate)/2,
        "total_gst_rate": gst_rate,
        "top_quote": top_quote,
    }
    
    # Render template to string
    template_name = "demo_template.html" if flag else "bill_template.html"
    html_content = render_to_string(template_name, context)
    
    # Create temporary HTML file
    with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as f:
        f.write(html_content.encode('utf-8'))
        temp_file_path = f.name
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            
            page.goto(f'file://{temp_file_path}', wait_until='networkidle')
            page.wait_for_load_state('networkidle')
            page.wait_for_timeout(1000)
            
            pdf_data = page.pdf(
                format='A4',
                print_background=True,
                margin={
                    "top": "0mm",
                    "right": "0mm",
                    "bottom": "0mm",
                    "left": "0mm",
                }
            )
            
            browser.close()
    finally:
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
    
    # Save PDF
    pdf_dir = os.path.join(settings.MEDIA_ROOT, 'invoices')
    os.makedirs(pdf_dir, exist_ok=True)
    
    pdf_filename = f"invoice-no-{invoice.invoice_number}-{formatted_datetime}.pdf"
    pdf_path = os.path.join(pdf_dir, pdf_filename)
    
    with open(pdf_path, 'wb') as f:
        f.write(pdf_data)
    
    response = HttpResponse(pdf_data, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{pdf_filename}"'
    return response

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
    invoices, total = invoice_helper.get_invoice_data(request)
    
    # Set up pagination - 10 items per page
    paginator = Paginator(invoices, 10)
    page = request.GET.get('page')
    
    try:
        invoices_page = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page
        invoices_page = paginator.page(1)
    except EmptyPage:
        # If page is out of range, deliver last page
        invoices_page = paginator.page(paginator.num_pages)
    
    data = {
        "invoices": invoices_page,
        "request": request,
        "total": total,
        "avg_value": total / paginator.count if paginator.count > 0 else 0,
    }
    return render(request, "invoice_display.html", data)

@csrf_exempt 
def edit_invoice(request, invoice_id):
    """
    View to edit an existing invoice
    """
    invoice = get_object_or_404(Invoice, id=invoice_id)
    
    if request.method == 'POST':
        try:
            # Update invoice fields
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
            
            # Save the updated invoice
            invoice.save()
            
            messages.success(request, f'Invoice #{invoice.invoice_number} has been updated successfully!')
            return redirect('billing:view_invoices')
            
        except Exception as e:
            messages.error(request, f'Error updating invoice: {str(e)}')
    
    # Get all related objects for dropdowns
    context = {
        'invoice': invoice,
        'vendor' : queries.get_vendor(request.user),
        'product' : queries.get_product(request.user),
        'company' : queries.get_company(request.user),
        'plant' : queries.get_plant(request.user),
        'vehicle' : queries.get_vehicle(request.user),
        'gst' : queries.get_gst(),
        'bank_details' :  queries.get_bank_details(request.user),
       }
    
    return render(request, 'edit_invoice.html', context)

@csrf_exempt 
@require_POST     
def delete_invoice(request, invoice_id):
    """
    View to delete an invoice
    """
    print(f"Deleting invoice: {invoice_id}")
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