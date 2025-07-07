from django.urls import path
from .views import generate_invoice, serve_temp_pdf, view_invoices, delete_invoice, edit_invoice
from django.conf import settings
from . import views
from django.conf.urls.static import static

app_name = 'billing'  # Add this line to create the namespace

urlpatterns = [
    path('invoice/', generate_invoice, name='generate_invoice'),
    path('temp-pdf/<str:cache_key>/', serve_temp_pdf, name='serve_temp_pdf'),
    path('view_invoices/', view_invoices, name='view_invoices'),  # Added trailing slash for consistency
    path('delete_invoice/<int:invoice_id>/', delete_invoice, name='delete_invoice'),  # Removed 'billing/' prefix
    path('edit_invoice/<int:invoice_id>/', edit_invoice, name='edit_invoice'),  # Removed 'billing/' prefix
    path('invoice/<int:pk>/', views.invoice_pdf_view, name='invoice-detail'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)