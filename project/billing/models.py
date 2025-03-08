from django.db import models
from vendor.models import Vendor, Plant
from product.models import Product
from company.models import Company

class Billing(models.Model):
    invoice_number = models.CharField(max_length=100)
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(auto_now_add=True)
    vendor = models.ForeignKey(Vendor, on_delete=models.PROTECT)
    plant = models.ForeignKey(Plant, on_delete=models.PROTECT)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    chalan_number = models.CharField(max_length=100)
    company = models.ForeignKey(Company, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Invoice {self.invoice_number} - Amount: {self.rate}'

class Invoice(models.Model):
    invoice_number = models.CharField(max_length=100, blank=True, null=True)
    rate = models.DecimalField(max_digits=10, decimal_places=2,blank=True, null=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2,blank=True, null=True)
    date = models.DateField(auto_now_add=True)
    vendor = models.ForeignKey(Vendor, on_delete=models.PROTECT,blank=True, null=True)
    plant = models.ForeignKey(Plant, on_delete=models.PROTECT,blank=True, null=True)
    product = models.ForeignKey(Product, on_delete=models.PROTECT,blank=True, null=True)
    chalan_number = models.CharField(max_length=100,blank=True, null=True)
    company = models.ForeignKey(Company, on_delete=models.PROTECT,blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2,blank=True, null=True)
    cgst = models.DecimalField(max_digits=10, decimal_places=2,blank=True, null=True)
    sgst = models.DecimalField(max_digits=10, decimal_places=2,blank=True, null=True)
    net_amount = models.DecimalField(max_digits=10, decimal_places=2,blank=True, null=True)
    amount_in_words = models.CharField(max_length=300,blank=True, null=True)

    def __str__(self):
        return f'Invoice {self.invoice_number}'