from django.db import models

class Vehicle(models.Model):
    make = models.CharField(max_length=100, blank=True)
    model = models.CharField(max_length=100, blank=True)
    number = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True )

    def __str__(self):
        return f"{self.number} "
