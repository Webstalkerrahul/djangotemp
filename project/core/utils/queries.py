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
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, date

def add_multi_line_invoice(user, invoice_number, vendor_id, line_items, gst_rate=12, bank_detail=None):
    """
    Create an invoice with multiple line items
    """
    try:
        with transaction.atomic():
            # Get vendor object
            try:
                vendor = Vendor.objects.get(id=vendor_id)
            except Vendor.DoesNotExist:
                raise ValueError(f"Vendor with ID {vendor_id} does not exist")
            
            # Get company information safely
            company = None
            try:
                # Based on your Company model: user -> Company (user field in Company)
                company = Company.objects.get(user=user)
            except Company.DoesNotExist:
                company = None
            except Exception as e:
                company = None
            
            # Calculate totals from line items
            total_amount = sum(
                Decimal(str(item.get('rate', 0))) * Decimal(str(item.get('quantity', 0))) 
                for item in line_items
            )
            
            # Calculate GST amounts
            gst_rate_decimal = Decimal(str(gst_rate)) / 100
            cgst = total_amount * (gst_rate_decimal / 2)  # Half of GST rate for CGST
            sgst = total_amount * (gst_rate_decimal / 2)  # Half of GST rate for SGST
            net_amount = total_amount + cgst + sgst
            
            # Get first line item for single-value fields (as per your original logic)
            first_item = line_items[0] if line_items else {}
            
            # Get related objects for the first item
            plant = None
            vehicle = None
            product = None
            
            if first_item.get('plant_id'):
                try:
                    plant = Plant.objects.get(id=first_item.get('plant_id'))
                except Plant.DoesNotExist:
                    pass
                    
            if first_item.get('vehicle_id'):
                try:
                    vehicle = Vehicle.objects.get(id=first_item.get('vehicle_id'))
                except Vehicle.DoesNotExist:
                    pass
                    
            if first_item.get('product_id'):
                try:
                    product = Product.objects.get(id=first_item.get('product_id'))
                except Product.DoesNotExist:
                    pass
            
            # Get bank detail object if provided
            bank_detail_obj = None
            if bank_detail:
                try:
                    bank_detail_obj = BankDetail.objects.get(id=bank_detail)
                except BankDetail.DoesNotExist:
                    pass
            
            # Create invoice data matching your Invoice model fields
            invoice_data = {
                'invoice_number': invoice_number,
                'vendor': vendor,
                'company': company,
                'date': timezone.now().date(),
                'total_amount': total_amount,
                'cgst': cgst,
                'sgst': sgst,
                'net_amount': net_amount,
                'amount_in_words': num_to_words_indian(round(net_amount)),
                'created_at': timezone.now(),
            }
            
            # Add optional fields from first line item
            if plant:
                invoice_data['plant'] = plant
            if vehicle:
                invoice_data['vehicle'] = vehicle
            if product:
                invoice_data['product'] = product
            if bank_detail_obj:
                invoice_data['bank_details'] = bank_detail_obj
                
            # Add rate and quantity (sum of all line items for quantity)
            invoice_data['rate'] = Decimal(str(first_item.get('rate', 0)))
            invoice_data['quantity'] = sum(Decimal(str(item.get('quantity', 0))) for item in line_items)
            invoice_data['chalan_number'] = first_item.get('chalan_number', '')

            print("Invoice data before creation:", invoice_data)
            
            # Create the invoice
            invoice = Invoice.objects.create(**invoice_data)
            
            # Create billing items for each line item
            for item in line_items:
                # Extract product information
                product_id = item.get('product_id')
                
                if not product_id:
                    raise ValueError(f"Missing product_id in line item: {item}")
                
                # Verify product exists and get object
                try:
                    product = Product.objects.get(id=product_id)
                except Product.DoesNotExist:
                    raise ValueError(f"Product with ID {product_id} does not exist")
                
                # Get other related objects
                plant_obj = None
                vehicle_obj = None
                
                if item.get('plant_id'):
                    try:
                        plant_obj = Plant.objects.get(id=item.get('plant_id'))
                    except Plant.DoesNotExist:
                        pass
                        
                if item.get('vehicle_id'):
                    try:
                        vehicle_obj = Vehicle.objects.get(id=item.get('vehicle_id'))
                    except Vehicle.DoesNotExist:
                        pass
                
                # Create billing record with ForeignKey objects
                billing_data = {
                    'invoice_number': invoice.invoice_number,
                    'chalan_number': item.get('chalan_number', ''),
                    'quantity': Decimal(str(item.get('quantity', 0))),
                    'rate': Decimal(str(item.get('rate', 0))),
                    'date': item.get('date') or timezone.now().date(),
                    'vendor': vendor,  # Use vendor object, not vendor_id
                    'product': product,  # Use product object
                    'company': company,  # Use company object
                    'created_at': timezone.now(),
                }
                
                # Add optional related objects
                if plant_obj:
                    billing_data['plant'] = plant_obj
                if vehicle_obj:
                    billing_data['vehicle'] = vehicle_obj

                print("Billing data before creation:", billing_data)
                
                billing_item = Billing.objects.create(**billing_data)
            
            return invoice
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise

def add_data_billing(invoice_number, chalan_number, rate, quantity, date_str, vendor_id, plant_id, product_id, company_id, vehicle_id, gst_rate=None):
    """
    Updated function to match your model structure
    """
    try:
        # Parse date
        if date_str:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        else:
            date_obj = date.today()
    
        # Get related objects
        vendor = Vendor.objects.get(id=vendor_id)
        plant = Plant.objects.get(id=plant_id)
        product = Product.objects.get(id=product_id)
        company = Company.objects.get(id=company_id)
        vehicle = Vehicle.objects.get(id=vehicle_id) if vehicle_id else None

        # Convert to Decimal for calculations
        rate_decimal = Decimal(str(rate))
        quantity_decimal = Decimal(str(quantity))
        total_amount = rate_decimal * quantity_decimal
        
        # Calculate GST
        if gst_rate:
            try:
                gst_rate_clean = clean_gst_rate(gst_rate)
                gst_decimal = Decimal(str(gst_rate_clean))
                cgst = total_amount * (gst_decimal / 2) / 100
                sgst = total_amount * (gst_decimal / 2) / 100
            except:
                cgst = total_amount * Decimal('0.025')  # 2.5% fallback
                sgst = total_amount * Decimal('0.025')  # 2.5% fallback
        else:
            cgst = total_amount * Decimal('0.025')  # 2.5%
            sgst = total_amount * Decimal('0.025')  # 2.5%

        # Calculate net_amount
        net_amount = total_amount + cgst + sgst

        # Convert net_amount to words
        words = num_to_words_indian(round(net_amount))
        
        # Create billing record first
        billing_data = {
            'invoice_number': invoice_number,
            'chalan_number': chalan_number,
            'rate': rate_decimal,
            'quantity': quantity_decimal,
            'date': date_obj,
            'vendor': vendor,  # Use object, not ID
            'plant': plant,    # Use object, not ID
            'product': product, # Use object, not ID
            'company': company, # Use object, not ID
        }
        
        if vehicle:
            billing_data['vehicle'] = vehicle
            
        billing = Billing.objects.create(**billing_data)
        
        # Create the Invoice object with ForeignKey objects
        invoice_data = {
            'invoice_number': invoice_number,
            'rate': rate_decimal,
            'quantity': quantity_decimal,
            'date': date_obj,
            'vendor': vendor,
            'plant': plant,
            'product': product,
            'chalan_number': chalan_number,
            'company': company,
            'total_amount': total_amount,
            'cgst': cgst,
            'sgst': sgst,
            'net_amount': net_amount,
            'amount_in_words': words,
        }
        
        if vehicle:
            invoice_data['vehicle'] = vehicle
            
        invoice = Invoice.objects.create(**invoice_data)
        
        return invoice
        
    except Exception as e:
        print(f"Error in add_data_billing: {e}")
        return None