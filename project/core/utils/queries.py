from billing.models import Billing, Invoice
from vendor.models import Vendor, Plant
from product.models import Product
from company.models import Company
from vehicle.models import Vehicle
from decimal import Decimal
from datetime import datetime, date
from num2words import num2words
from .amount_to_words import num_to_words_indian

def get_vendor(logged_in_user):
    if logged_in_user.is_superuser:
        return Vendor.objects.all()
    return Vendor.objects.filter(user=logged_in_user)

def get_product(logged_in_user):
    if logged_in_user.is_superuser:
        return Product.objects.all()
    return Product.objects.filter(user=logged_in_user)

def get_company(logged_in_user):
    if logged_in_user.is_superuser:
        return Company.objects.all()
    return Company.objects.filter(user=logged_in_user)

def get_plant(logged_in_user):
    if logged_in_user.is_superuser:
        return Plant.objects.all()
    return Plant.objects.filter(user=logged_in_user)

def get_billing():
    return Billing.objects.all()

def get_vehicle(logged_in_user):
    if logged_in_user.is_superuser:
        return Vehicle.objects.all()
    return Vehicle.objects.filter(user=logged_in_user)

def add_data_billing(invoice_number, chalan_number, rate, quantity, date_str, vendor_id, plant_id, product_id, company_id, vehicle_id):
    try:
        if date_str:
            date_str = datetime.strptime(date_str, "%Y-%m-%d").date()
        else:
            date_str = date.today()
    
        billing =  Billing.objects.create(invoice_number=invoice_number, chalan_number=chalan_number, rate=rate, quantity=quantity, date=date_str, vendor_id=vendor_id, plant_id=plant_id, product_id=product_id, company_id=company_id, vehicle_id=vehicle_id)

        vendor = Vendor.objects.get(id=vendor_id)
        plant = Plant.objects.get(id=plant_id)
        product = Product.objects.get(id=product_id)
        company = Company.objects.get(id=company_id)
        vehicle = Vehicle.objects.get(id=vehicle_id)

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
        print("here",date_str)
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
            amount_in_words=words,
            vehicle = vehicle
        )
        # Save the object to the database
        return invoice
    except Exception as e:
        print(f"Error adding data: {e}")
        return None

