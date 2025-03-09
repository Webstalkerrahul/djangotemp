from billing.models import Billing, Invoice
from vendor.models import Vendor, Plant
from product.models import Product
from company.models import Company
from decimal import Decimal
from num2words import num2words
from .amount_to_words import num_to_words_indian

def get_vendor():
    return Vendor.objects.all()

def get_product():
    return Product.objects.all()

def get_company():
    return Company.objects.all()

def get_plant():
    return Plant.objects.all()

def get_billing():
    return Billing.objects.all()

def add_data_billing(invoice_number, chalan_number, rate, quantity, date_str, vendor_id, plant_id, product_id, company_id):
    try:
        billing =  Billing.objects.create(invoice_number=invoice_number, chalan_number=chalan_number, rate=rate, quantity=quantity, date=date_str, vendor_id=vendor_id, plant_id=plant_id, product_id=product_id, company_id=company_id)

        vendor = Vendor.objects.get(id=vendor_id)
        plant = Plant.objects.get(id=plant_id)
        product = Product.objects.get(id=product_id)
        company = Company.objects.get(id=company_id)

        rate = Decimal(rate)  # Convert rate to Decimal
        quantity = Decimal(quantity)  # Convert quantity to Decimal
        total_amount= rate * quantity
        cgst=total_amount * Decimal('0.025')
        sgst=total_amount * Decimal('0.025')

        # Calculate net_amount
        net_amount = Decimal(total_amount) + cgst + sgst

        # Convert net_amount to words
        # words = num2words(net_amount, to="currency", lang="en_IN")
        words = num_to_words_indian(round(net_amount))
        # Create the Invoice object
        invoice = Invoice.objects.create(
            invoice_number=invoice_number,
            rate=rate,
            quantity=quantity,
            date=date_str,
            vendor=vendor,
            plant=plant,
            product=product,
            chalan_number=chalan_number,
            company=company,
            total_amount=total_amount,
            cgst=cgst,
            sgst=sgst,
            net_amount=net_amount,
            amount_in_words=words
        )
        # Save the object to the database
        return invoice
    except Exception as e:
        print(f"Error adding data: {e}")
        return None

