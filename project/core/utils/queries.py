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
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist

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

def add_multi_line_invoice(user, invoice_number, vendor_id, line_items, gst_rate=12, bank_detail=None):
    """
    Create an invoice with multiple line items
    """
    try:
        with transaction.atomic():
            # Create the main invoice record with only valid fields
            invoice_data = {
                'invoice_number': invoice_number,
                'vendor_id': vendor_id,
            }
            
            # Get company information safely
            company = None
            try:
                # Based on your Company model: user -> Company (user field in Company)
                company = Company.objects.get(user=user)
                print(f"Found company for user {user.username}: {company.name}")
            except Company.DoesNotExist:
                print(f"No company found for user: {user.username}")
                company = None
            except Exception as e:
                print(f"Error getting company for user: {e}")
                company = None
            
            # Only add fields that exist in your Invoice model
            invoice_fields = [f.name for f in Invoice._meta.fields]
            
            if 'user' in invoice_fields:
                invoice_data['user'] = user
            elif 'created_by' in invoice_fields:
                invoice_data['created_by'] = user
            elif 'user_id' in invoice_fields:
                invoice_data['user_id'] = user.id
                
            if 'gst_rate' in invoice_fields:
                invoice_data['gst_rate'] = gst_rate
                
            if 'bank_detail' in invoice_fields:
                invoice_data['bank_detail'] = bank_detail
                
            if 'company' in invoice_fields and company:
                invoice_data['company'] = company
            elif 'company_id' in invoice_fields and company:
                invoice_data['company_id'] = company.id
                
            if 'date' in invoice_fields:
                invoice_data['date'] = timezone.now().date()
                
            if 'total_amount' in invoice_fields:
                invoice_data['total_amount'] = sum(float(item.get('amount', 0)) for item in line_items)
            
            print(f"Creating invoice with data: {invoice_data}")
            
            # Create the invoice
            invoice = Invoice.objects.create(**invoice_data)
            
            # Create billing items for each line item
            for item in line_items:
                # Extract product information
                product_id = item.get('product_id')
                
                if not product_id:
                    raise ValueError(f"Missing product_id in line item: {item}")
                
                # Verify product exists
                try:
                    product = Product.objects.get(id=product_id)
                except Product.DoesNotExist:
                    raise ValueError(f"Product with ID {product_id} does not exist")
                
                # Create billing record
                billing_data = {
                    'invoice_number': invoice.invoice_number,
                    'chalan_number': item.get('chalan_number', ''),
                    'quantity': item.get('quantity', 0),
                    'rate': item.get('rate', 0),
                    'date': item.get('date'),
                    'vendor_id': vendor_id,
                    'product_id': product_id,
                    'plant_id': item.get('plant_id'),
                    'vehicle_id': item.get('vehicle_id'),
                    'created_at': timezone.now(),
                }
                
                # Add company field if it exists in Billing model
                billing_fields = [f.name for f in Billing._meta.fields]
                if 'company' in billing_fields and company:
                    billing_data['company'] = company
                elif 'company_id' in billing_fields and company:
                    billing_data['company_id'] = company.id
                
                print(f"Creating billing item with data: {billing_data}")
                
                billing_item = Billing.objects.create(**billing_data)
                
                print(f"Created billing item: ID={billing_item.id}, Product={product_id}")
            
            return invoice
            
    except Exception as e:
        print(f"Error in add_multi_line_invoice: {e}")
        import traceback
        traceback.print_exc()
        raise

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