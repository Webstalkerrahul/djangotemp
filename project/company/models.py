from django.db import models

class Company(models.Model):
    name = models.CharField(max_length=255, blank=True)
    tagline = models.CharField(max_length=255, blank=True)
    address = models.TextField(blank=True)
    email = models.EmailField(blank=True)
    phone_number = models.CharField(max_length=20,blank=True)
    gst_details = models.CharField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.name

class BankDetail(models.Model):
    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name='bank_details')
    bank_name = models.CharField(max_length=255, null=True, blank=True)
    account_number = models.CharField(max_length=50,  null=True, blank=True)
    ifsc_code = models.CharField(max_length=20,  null=True, blank=True)
    branch = models.CharField(max_length=255, blank=True, null=True)
    account_holder_name = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.bank_name}"