from django.db import models
from vendor.models import Vendor, Plant
from product.models import Product
from company.models import Company

class Billing(models.Model):
    invoice_number = models.CharField(max_length=100)
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField(max_length=10)
    date = models.DateField(auto_now_add=True)
    vendor = models.ForeignKey(Vendor, on_delete=models.PROTECT)
    plant = models.ForeignKey(Plant, on_delete=models.PROTECT)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    company = models.ForeignKey(Company, on_delete=models.PROTECT)

    def __str__(self):
        return f'Invoice {self.invoice_number} - Amount: {self.amount}'
