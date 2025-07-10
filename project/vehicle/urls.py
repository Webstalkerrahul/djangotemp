from django.urls import path
from . import views

app_name = 'vehicles'

urlpatterns = [
    path('vehicles/', views.vehicle_list, name='vehicle_list'),
    path('add/', views.add_vehicle, name='add_vehicle'),
    path('edit/<int:vehicle_id>/', views.edit_vehicle, name='edit_vehicle'),
    path('view/<int:vehicle_id>/', views.view_vehicle, name='view_vehicle'),
    path('delete/<int:vehicle_id>/', views.delete_vehicle, name='delete_vehicle'),
    path('search/', views.vehicle_search, name='vehicle_search'),
    path('statistics/', views.vehicle_statistics, name='vehicle_statistics'),
    path('bulk-delete/', views.bulk_delete_vehicles, name='bulk_delete_vehicles'),
]