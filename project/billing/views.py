from django.shortcuts import render
from django.http import HttpResponse
from django.template.loader import render_to_string
from playwright.sync_api import sync_playwright
import tempfile
import os
import base64
from django.conf import settings
from core.utils import queries

def generate_invoice(request):
    # You can add context data here if needed
    if request.method == 'POST':
         # Get form data
            invoice_number = request.POST.get('invoice_number')
            chalan_number = request.POST.get('chalan_number')
            rate = request.POST.get('rate')
            quantity = request.POST.get('quantity')
            date_str = request.POST.get('date')
            vendor_id = request.POST.get('vendor')
            plant_id = request.POST.get('plant')
            product_id = request.POST.get('product')
            company_id = request.POST.get('company')

            invoice = queries.add_data_billing(invoice_number, chalan_number, rate, quantity, date_str, vendor_id, plant_id, product_id, company_id)
            if invoice is None:
                return render(request, 'billing.html', {'error': 'Error adding data'})
            else:
                response = render_invoice_pdf(invoice)
            
                return response
            
    vendor = queries.get_vendor()
    product = queries.get_product()
    company = queries.get_company()
    plant = queries.get_plant()

    return render(request, 'billing.html', {'vendors': vendor, 'products': product, 'company': company, 'plants': plant})

def render_invoice_pdf(invoice):
    logo_path = os.path.join(settings.BASE_DIR, 'billing/static', 'logo.png')
    with open(logo_path, "rb") as image_file:
        encoded_logo = base64.b64encode(image_file.read()).decode('utf-8')
    
    # Create data URL for the image
    logo_data_url = f"data:image/png;base64,{encoded_logo}"
   
    context = {
        "invoice": invoice,
        "logo_data_url": logo_data_url,
        # Add any other context variables needed
    }
    
    # Render template to string
    html_content = render_to_string("bill_template.html", context)
    
    # Create a temporary HTML file to ensure all resources load properly
    with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as f:
        f.write(html_content.encode('utf-8'))
        temp_file_path = f.name
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            
            # Navigate to the file with proper waiting for resources
            page.goto(f'file://{temp_file_path}', wait_until='networkidle')
            
            # Wait for Tailwind to be loaded and applied
            page.wait_for_load_state('networkidle')
            page.wait_for_timeout(1000)  # Additional 1s wait for any JS processing
            
            # Generate PDF with proper formatting for A4
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
        # Clean up the temporary file
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
    
    # Return the PDF as a response
    response = HttpResponse(pdf_data, content_type="application/pdf")
    response["Content-Disposition"] = 'inline; filename="invoice.pdf"'
    return response

