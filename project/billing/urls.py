from django.urls import path
from .views import generate_invoice, serve_temp_pdf
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path('invoice/', generate_invoice, name='generate_invoice'),  # Example URL for invoice
    # In your urls.py
    path('billing/temp-pdf/<str:cache_key>/', serve_temp_pdf, name='serve_temp_pdf'),
    # path('pdf/', generate_pdf, name='generate_pdf'),  # Example URL for PDF generation
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)