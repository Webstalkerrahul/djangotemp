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
    
        billing = Billing.objects.create(invoice_number=invoice_number, chalan_number=chalan_number, rate=rate, quantity=quantity, date=date_str, vendor_id=vendor_id, plant_id=plant_id, product_id=product_id, company_id=company_id, vehicle_id=vehicle_id)

        vendor = Vendor.objects.get(id=vendor_id)
        plant = Plant.objects.get(id=plant_id)
        product = Product.objects.get(id=product_id)
        company = Company.objects.get(id=company_id)
        vehicle = Vehicle.objects.get(id=vehicle_id)

        rate = Decimal(rate)  # Convert rate to Decimal
        quantity = Decimal(quantity)  # Convert quantity to Decimal
        total_amount = rate * quantity
        cgst = total_amount * Decimal('0.025')
        sgst = total_amount * Decimal('0.025')

        # Calculate net_amount
        net_amount = Decimal(total_amount) + cgst + sgst

        # Convert net_amount to words
        words = num_to_words_indian(round(net_amount))
        print("here", date_str)
        
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
            vehicle=vehicle
        )
        # Save the object to the database
        return invoice
    except Exception as e:
        print(f"Error adding data: {e}")
        return None

def add_multi_line_invoice(invoice_number, vendor_id, line_items):
    """
    Create an invoice with multiple line items
    
    Args:
        invoice_number: Unique invoice number
        vendor_id: ID of the vendor
        line_items: List of dictionaries containing line item data
                   Each dict should have: date, chalan_number, vehicle_id, product_id, quantity, rate, amount
    
    Returns:
        Invoice object with items attribute containing all line items
    """
    try:
        # Get vendor and first line item for basic invoice info
        vendor = Vendor.objects.get(id=vendor_id)
        
        if not line_items:
            raise ValueError("No line items provided")
        
        # Calculate totals
        total_amount = Decimal('0')
        invoice_items = []
        
        for item_data in line_items:
            # Parse date
            if isinstance(item_data['date'], str):
                item_date = datetime.strptime(item_data['date'], "%Y-%m-%d").date()
            else:
                item_date = item_data['date']
            
            # Get related objects
            vehicle = Vehicle.objects.get(id=item_data['vehicle_id'])
            product = Product.objects.get(id=item_data['product_id'])
            
            # Calculate amount
            quantity = Decimal(str(item_data['quantity']))
            rate = Decimal(str(item_data['rate']))
            amount = quantity * rate
            
            total_amount += amount
            
            # Create invoice item object (this will be attached to the invoice)
            invoice_item = {
                'date': item_date,
                'chalan_number': item_data['chalan_number'],
                'vehicle': vehicle,
                'product': product,
                'quantity': quantity,
                'rate': rate,
                'amount': amount
            }
            invoice_items.append(invoice_item)
        
        # Calculate taxes
        cgst = total_amount * Decimal('0.025')
        sgst = total_amount * Decimal('0.025')
        net_amount = total_amount + cgst + sgst
        
        # Convert net_amount to words
        words = num_to_words_indian(round(net_amount))
        
        # Get company (assuming first available company for now)
        # You might want to pass company_id as a parameter
        company = Company.objects.first()
        
        # Create main invoice record using first line item's data
        first_item = line_items[0]
        first_item_date = datetime.strptime(first_item['date'], "%Y-%m-%d").date() if isinstance(first_item['date'], str) else first_item['date']
        
        invoice = Invoice.objects.create(
            invoice_number=invoice_number,
            rate=Decimal(str(first_item['rate'])),  # Using first item's rate as representative
            quantity=sum(Decimal(str(item['quantity'])) for item in line_items),  # Total quantity
            date=first_item_date,  # Using first item's date
            vendor=vendor,
            plant=Plant.objects.first(),  # You might want to handle this differently
            product=Product.objects.get(id=first_item['product_id']),
            chalan_number=first_item['chalan_number'],  # Using first item's challan
            company=company,
            total_amount=total_amount,
            cgst=cgst,
            sgst=sgst,
            net_amount=net_amount,
            amount_in_words=words,
            vehicle=Vehicle.objects.get(id=first_item['vehicle_id'])
        )
        
        # Attach line items to invoice object (for template usage)
        invoice.items = invoice_items
        
        # Create individual Billing records for each line item
        for item_data in line_items:
            item_date = datetime.strptime(item_data['date'], "%Y-%m-%d").date() if isinstance(item_data['date'], str) else item_data['date']
            
            Billing.objects.create(
                invoice_number=f"{invoice_number}-{item_data['chalan_number']}",
                chalan_number=item_data['chalan_number'],
                rate=Decimal(str(item_data['rate'])),
                quantity=Decimal(str(item_data['quantity'])),
                date=item_date,
                vendor_id=vendor_id,
                plant_id=Plant.objects.first().id,  # You might want to handle this differently
                product_id=item_data['product_id'],
                company_id=company.id,
                vehicle_id=item_data['vehicle_id']
            )
        
        return invoice
        
    except Exception as e:
        print(f"Error creating multi-line invoice: {e}")
        return None