from django.db import models

class Vendor(models.Model):
    name = models.CharField(max_length=200, blank=True)
    email = models.EmailField(unique=True, null=True,blank=True)
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    vendor_code = models.CharField(max_length=50, null=True, unique=True)
    gst_number = models.CharField(max_length=100, null=True, blank=True)
    pincode = models.CharField(max_length=10, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)
    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-created_at']



class Plant(models.Model):
    name = models.CharField(max_length=200,null=True, blank=True)
    email = models.EmailField(unique=True,null=True, blank=True)
    phone = models.CharField(max_length=15,null=True, blank=True)
    address = models.TextField(blank=True, null=True)
    vendor = models.ForeignKey(Vendor, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)
    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-created_at']