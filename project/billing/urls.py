from django.urls import path
from .views import generate_invoice, serve_temp_pdf, view_invoices
from django.conf import settings
from django.conf.urls.static import static

app_name = 'billing'  # Add this line to create the namespace

urlpatterns = [
    path('invoice/', generate_invoice, name='generate_invoice'),  # Example URL for invoice
    # In your urls.py
    path('billing/temp-pdf/<str:cache_key>/', serve_temp_pdf, name='serve_temp_pdf'),
    # path('pdf/', generate_pdf, name='generate_pdf'),  # Example URL for PDF generation
    path('billing/view_invoices', view_invoices, name='view_invoices'),
    # path('invoices/ajax/', load_invoices_ajax, name='load_invoices_ajax'),

]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)