from billing.models import Billing, Invoice, GST
from vendor.models import Vendor, Plant
from product.models import Product
from company.models import Company, BankDetail
from vehicle.models import Vehicle
from decimal import Decimal, InvalidOperation
from datetime import datetime, date
from num2words import num2words
from .amount_to_words import num_to_words_indian
import re

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

def get_gst():
    return GST.objects.all()

def get_bank_details(logged_in_user):
    if logged_in_user.is_superuser:
        return BankDetail.objects.all()
    return BankDetail.objects.filter(user=logged_in_user)

def clean_gst_rate(gst_rate):
    """
    Clean and validate GST rate input
    """
    if gst_rate is None:
        return "12"  # Default GST rate
    
    # Convert to string and clean
    rate_str = str(gst_rate).strip()
    
    # Remove any currency symbols, percentage signs, or other characters
    cleaned = re.sub(r'[^\d.]', '', rate_str)
    
    # Handle empty string
    if not cleaned or cleaned == '.':
        return "12"
    
    # Validate it's a valid number
    try:
        float(cleaned)
        return cleaned
    except ValueError:
        return "12"

def add_multi_line_invoice(user, invoice_number, vendor_id, line_items, gst_rate, bank_detail):
    """
    Create an invoice with multiple line items
    
    Args:
        invoice_number: Unique invoice number
        vendor_id: ID of the vendor
        line_items: List of dictionaries containing line item data
                   Each dict should have: date, chalan_number, vehicle_id, product_id, quantity, rate, amount
        gst_rate: GST rate (can be string with % or decimal)
        bank_detail: Bank detail ID
    
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
            plant = Plant.objects.get(id=item_data['plant_id'])
            
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
                'plant': plant,
                'quantity': quantity,
                'rate': rate,
                'amount': amount
            }
            invoice_items.append(invoice_item)
        
        # Calculate taxes with proper error handling
        try:
            
            # Clean the GST rate
            gst_rate_clean = clean_gst_rate(gst_rate)
            
            # Convert to Decimal safely
            gst_decimal = Decimal(gst_rate_clean)
            
            # Calculate CGST and SGST (each is half of total GST)
            cgst = total_amount * (gst_decimal / 2) / 100
            sgst = total_amount * (gst_decimal / 2) / 100
            net_amount = total_amount + cgst + sgst
            
        except (InvalidOperation, ValueError) as e:
            print(f"Error with GST rate '{gst_rate}': {e}")
            print("Using default 12% GST rate")
            
            # Fallback calculation with 12% GST (6% CGST + 6% SGST)
            cgst = total_amount * Decimal('6') / 100
            sgst = total_amount * Decimal('6') / 100
            net_amount = total_amount + cgst + sgst
        
        # Convert net_amount to words
        words = num_to_words_indian(round(net_amount))
        
        # Get company (assuming first available company for now)
        # You might want to pass company_id as a parameter
        company = Company.objects.filter(user=user).first()
        print(company.name)
        
        # Create main invoice record using first line item's data
        first_item = line_items[0]
        first_item_date = datetime.strptime(first_item['date'], "%Y-%m-%d").date() if isinstance(first_item['date'], str) else first_item['date']
        
        invoice = Invoice.objects.create(
            invoice_number=invoice_number,
            rate=Decimal(str(first_item['rate'])),  # Using first item's rate as representative
            quantity=sum(Decimal(str(item['quantity'])) for item in line_items),  # Total quantity
            date=first_item_date,  # Using first item's date
            vendor=vendor,
            plant=Plant.objects.get(id=first_item['plant_id']),  # You might want to handle this differently
            product=Product.objects.get(id=first_item['product_id']),
            chalan_number=first_item['chalan_number'],  # Using first item's challan
            company=company,
            total_amount=total_amount,
            cgst=cgst,
            sgst=sgst,
            net_amount=net_amount,
            amount_in_words=words,
            vehicle=Vehicle.objects.get(id=first_item['vehicle_id']),
            bank_details=BankDetail.objects.get(id=bank_detail) if bank_detail else None
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
        print(f"Error type: {type(e).__name__}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return None

# Also update your original add_data_billing function for consistency
def add_data_billing(invoice_number, chalan_number, rate, quantity, date_str, vendor_id, plant_id, product_id, company_id, vehicle_id, gst_rate=None):
    try:
        if date_str:
            date_str = datetime.strptime(date_str, "%Y-%m-%d").date()
        else:
            date_str = date.today()
    
        billing = Billing.objects.create(
            invoice_number=invoice_number, 
            chalan_number=chalan_number, 
            rate=rate, 
            quantity=quantity, 
            date=date_str, 
            vendor_id=vendor_id, 
            plant_id=plant_id, 
            product_id=product_id, 
            company_id=company_id, 
            vehicle_id=vehicle_id
        )

        vendor = Vendor.objects.get(id=vendor_id)
        plant = Plant.objects.get(id=plant_id)
        product = Product.objects.get(id=product_id)
        company = Company.objects.get(id=company_id)
        vehicle = Vehicle.objects.get(id=vehicle_id)

        rate = Decimal(rate)  # Convert rate to Decimal
        quantity = Decimal(quantity)  # Convert quantity to Decimal
        total_amount = rate * quantity
        
        # Use dynamic GST rate if provided, otherwise default to 5% (2.5% each)
        if gst_rate:
            try:
                gst_rate_clean = clean_gst_rate(gst_rate)
                gst_decimal = Decimal(gst_rate_clean)
                cgst = total_amount * (gst_decimal / 2) / 100
                sgst = total_amount * (gst_decimal / 2) / 100
            except:
                cgst = total_amount * Decimal('0.025')  # 2.5% fallback
                sgst = total_amount * Decimal('0.025')  # 2.5% fallback
        else:
            cgst = total_amount * Decimal('0.025')  # 2.5%
            sgst = total_amount * Decimal('0.025')  # 2.5%

        # Calculate net_amount
        net_amount = Decimal(total_amount) + cgst + sgst

        # Convert net_amount to words
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
            amount_in_words=words,
            vehicle=vehicle
        )
        # Save the object to the database
        return invoice
    except Exception as e:
        print(f"Error adding data: {e}")
        return None