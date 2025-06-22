
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
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
from django.views.decorators.csrf import csrf_exempt
from core.utils.sql import invoice_helper
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

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


def view_invoices(request):
    invoices = invoice_helper.get_invoice_data(request)
    
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
    }
    return render(request, "invoice_display.html", data)