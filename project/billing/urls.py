from django.urls import path
from .views import generate_invoice

urlpatterns = [
    path('invoice/', generate_invoice, name='generate_invoice'),  # Example URL for invoice
]
