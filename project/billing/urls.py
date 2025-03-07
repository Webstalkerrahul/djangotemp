from django.urls import path
from . import views  # Import your views

urlpatterns = [
    path('invoice/', views.invoice_view, name='invoice'),  # Example URL for invoice
]
