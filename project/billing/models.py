from django.db import models
from vendor.models import Vendor, Plant
from product.models import Product
from company.models import Company, BankDetail
from vehicle.models import Vehicle
from datetime import date

class Billing(models.Model):
    invoice_number = models.CharField(max_length=100)
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(default=date.today, blank=True, null=True)
    vendor = models.ForeignKey(Vendor, on_delete=models.SET_NULL, null=True, blank=True)
    plant = models.ForeignKey(Plant, on_delete=models.PROTECT, db_column='plant_id')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, db_column='product_id')
    vehicle = models.ForeignKey(
        Vehicle, 
        on_delete=models.PROTECT, 
        blank=True, 
        null=True,
        db_column='vehicle_id'  # Explicit column mapping
    )
    chalan_number = models.CharField(max_length=100)
    company = models.ForeignKey(Company, on_delete=models.PROTECT, db_column='company_id')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'billing_billing'  # Explicit table name

    def __str__(self):
        return f'Invoice {self.invoice_number} - Amount: {self.rate}'


class Invoice(models.Model):
    invoice_number = models.CharField(max_length=100, blank=True, null=True)
    rate = models.DecimalField(max_digits=10, decimal_places=2,blank=True, null=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2,blank=True, null=True)
    date = models.DateField(default=date.today, blank=True, null=True)
    vendor = models.ForeignKey(Vendor, on_delete=models.SET_NULL, null=True, blank=True)
    plant = models.ForeignKey(Plant, on_delete=models.PROTECT,blank=True, null=True)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.PROTECT,blank=True, null=True)
    product = models.ForeignKey(Product, on_delete=models.PROTECT,blank=True, null=True)
    chalan_number = models.CharField(max_length=100,blank=True, null=True)
    company = models.ForeignKey(Company, on_delete=models.PROTECT,blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2,blank=True, null=True)
    cgst = models.DecimalField(max_digits=10, decimal_places=2,blank=True, null=True)
    sgst = models.DecimalField(max_digits=10, decimal_places=2,blank=True, null=True)
    net_amount = models.DecimalField(max_digits=10, decimal_places=2,blank=True, null=True)
    amount_in_words = models.CharField(max_length=300,blank=True, null=True)
    bank_details = models.ForeignKey(BankDetail, on_delete=models.PROTECT,blank=True, null=True)
    pdf = models.FileField(upload_to="invoices/", blank=True, null=True)
    is_paid = models.BooleanField(default=False, blank=True, null=True)

    # Add payment status field

    def __str__(self):
        return f'Invoice {self.invoice_number}'
    
class GST(models.Model):
    cgst = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    sgst = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    total_gst = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    def __str__(self):
        return f'GST {self.total_gst}'