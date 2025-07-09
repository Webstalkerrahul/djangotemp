from django.urls import path
from .views import display_vendors, add_vendor_manual, display_plants, add_plant_manual, edit_vendor, delete_vendor, edit_plant, delete_plant
from django.conf import settings
from django.conf.urls.static import static

app_name = 'vendor'  # Add this line to create the namespace

urlpatterns = [
    path('vendor/', display_vendors, name='display_vendors'),  # Example URL for invoice
    path("add/", add_vendor_manual, name="add_vendor_manual"),
    path('plant/', display_plants, name='display_plants'),  # Example URL for invoice
    path("add_plant/", add_plant_manual, name="add_plant_manual"),
    path('<int:vendor_id>/edit/', edit_vendor, name='edit_vendor'),
    path('<int:vendor_id>/delete/', delete_vendor, name='delete_vendor'),
    # path('<int:vendor_id>/detail/', vendor_detail, name='vendor_detail'),

      # Plant URLs
    path('plant/', display_plants, name='display_plants'),
    path("add_plant/", add_plant_manual, name="add_plant_manual"),
    path('plant/<int:plant_id>/edit/', edit_plant, name='edit_plant'),
    path('plant/<int:plant_id>/delete/', delete_plant, name='delete_plant'),

]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)