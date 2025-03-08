from django.shortcuts import render
from num2words import num2words
from decimal import Decimal
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

            response = queries.add_data_billing(invoice_number, chalan_number, rate, quantity, date_str, vendor_id, plant_id, product_id, company_id)
            if response is None:
                return render(request, 'billing.html', {'error': 'Error adding data'})
            else:
                return render(request, 'billing.html', {'success': 'Data added successfully'})
    vendor = queries.get_vendor()
    product = queries.get_product()
    company = queries.get_company()
    plant = queries.get_plant()

    return render(request, 'billing.html', {'vendors': vendor, 'products': product, 'company': company, 'plants': plant})

def invoice_view(request):
    # # You can add context data here if needed
    # bills = Billing.objects.order_by('-created_at').first()
    # total_amount = bills.rate * bills.quantity
    # cgst = total_amount *  Decimal('0.025')
    # sgst = total_amount *  Decimal('0.025')
    # net_amount = total_amount + cgst + sgst
    # print(num2words(net_amount))

    return render(request, 'billing.html')
