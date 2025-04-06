from django.db import models

class Product(models.Model):
    name = models.CharField(max_length=255,blank=True)
    description = models.TextField(blank=True)
    hsn_code = models.CharField(max_length=100,blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.name
