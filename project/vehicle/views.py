from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Vehicle

@login_required
def vehicle_list(request):
    """
    Display paginated list of vehicles with search functionality and statistics
    """
    
    # Get search query from request
    search_query = request.GET.get('search', '').strip()
    
    # Base queryset - all vehicles for the current user
    vehicles_queryset = Vehicle.objects.filter(user=request.user)
    
    # Apply search filter if search query exists
    if search_query:
        vehicles_queryset = vehicles_queryset.filter(
            Q(number__icontains=search_query) |
            Q(make__icontains=search_query) |
            Q(model__icontains=search_query)
        )
    
    # Order by most recently updated
    vehicles_queryset = vehicles_queryset.order_by('-updated_at')
    
    # Calculate statistics
    total_vehicles = Vehicle.objects.filter(user=request.user).count()
    
    # Get unique makes and models
    unique_makes = Vehicle.objects.filter(user=request.user).values('make').distinct().count()
    unique_models = Vehicle.objects.filter(user=request.user).values('model').distinct().count()
    
    # Calculate recent vehicles (added in the last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_vehicles = Vehicle.objects.filter(
        user=request.user,
        created_at__gte=thirty_days_ago
    ).count()
    
    # Pagination
    paginator = Paginator(vehicles_queryset, 10)  # Show 10 vehicles per page
    page_number = request.GET.get('page')
    vehicles = paginator.get_page(page_number)
    
    # Context data for template
    context = {
        'vehicles': vehicles,
        'search_query': search_query,
        'total_vehicles': total_vehicles,
        'unique_makes': unique_makes,
        'unique_models': unique_models,
        'recent_vehicles': recent_vehicles,
        'page_title': 'Vehicle Management',
    }
    
    return render(request, 'vehicle_list.html', context)


@login_required
def add_vehicle(request):
    """
    Add a new vehicle
    """
    if request.method == 'POST':
        make = request.POST.get('make', '').strip()
        model = request.POST.get('model', '').strip()
        number = request.POST.get('number', '').strip()
        
        # Validation
        if not number:
            messages.error(request, 'Vehicle number is required')
            return render(request, 'vehicles/add_vehicle.html', {
                'make': make,
                'model': model,
                'number': number
            })
        
        # Check if vehicle number already exists for this user
        if Vehicle.objects.filter(user=request.user, number=number).exists():
            messages.error(request, f'Vehicle with number "{number}" already exists')
            return render(request, 'vehicles/add_vehicle.html', {
                'make': make,
                'model': model,
                'number': number
            })
        
        try:
            vehicle = Vehicle.objects.create(
                make=make,
                model=model,
                number=number,
                user=request.user
            )
            messages.success(request, f'Vehicle "{number}" has been added successfully!')
            return redirect('vehicles:vehicle_list')
            
        except Exception as e:
            messages.error(request, f'Error creating vehicle: {str(e)}')
            return render(request, 'vehicles/add_vehicle.html', {
                'make': make,
                'model': model,
                'number': number
            })
    
    # GET request - show form
    return render(request, 'add_vehicle.html')


@login_required
def edit_vehicle(request, vehicle_id):
    """
    Edit an existing vehicle
    """
    vehicle = get_object_or_404(Vehicle, id=vehicle_id, user=request.user)
    
    if request.method == 'POST':
        make = request.POST.get('make', '').strip()
        model = request.POST.get('model', '').strip()
        number = request.POST.get('number', '').strip()
        
        # Validation
        if not number:
            messages.error(request, 'Vehicle number is required')
            return render(request, 'vehicles/edit_vehicle.html', {
                'vehicle': vehicle,
                'make': make,
                'model': model,
                'number': number
            })
        
        # Check if vehicle number already exists for this user (excluding current vehicle)
        if Vehicle.objects.filter(user=request.user, number=number).exclude(id=vehicle_id).exists():
            messages.error(request, f'Vehicle with number "{number}" already exists')
            return render(request, 'vehicles/edit_vehicle.html', {
                'vehicle': vehicle,
                'make': make,
                'model': model,
                'number': number
            })
        
        try:
            vehicle.make = make
            vehicle.model = model
            vehicle.number = number
            vehicle.save()
            
            messages.success(request, f'Vehicle "{number}" has been updated successfully!')
            return redirect('vehicles:vehicle_list')
            
        except Exception as e:
            messages.error(request, f'Error updating vehicle: {str(e)}')
            return render(request, 'vehicles/edit_vehicle.html', {
                'vehicle': vehicle,
                'make': make,
                'model': model,
                'number': number
            })
    
    # GET request - show form with current data
    return render(request, 'edit_vehicle.html', {'vehicle': vehicle})


@login_required
def view_vehicle(request, vehicle_id):
    """
    View vehicle details
    """
    vehicle = get_object_or_404(Vehicle, id=vehicle_id, user=request.user)
    
    context = {
        'vehicle': vehicle,
        'page_title': f'Vehicle Details - {vehicle.number}',
    }
    
    return render(request, 'view_vehicle.html', context)


@login_required
def delete_vehicle(request, vehicle_id):
    """
    Delete a vehicle
    """
    vehicle = get_object_or_404(Vehicle, id=vehicle_id, user=request.user)
    
    if request.method == 'POST':
        vehicle_number = vehicle.number
        try:
            vehicle.delete()
            messages.success(request, f'Vehicle "{vehicle_number}" has been deleted successfully!')
        except Exception as e:
            messages.error(request, f'Error deleting vehicle: {str(e)}')
    
    return redirect('vehicles:vehicle_list')


@login_required
def vehicle_search(request):
    """
    AJAX endpoint for vehicle search
    """
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        search_query = request.GET.get('q', '').strip()
        
        if search_query:
            vehicles = Vehicle.objects.filter(
                user=request.user
            ).filter(
                Q(number__icontains=search_query) |
                Q(make__icontains=search_query) |
                Q(model__icontains=search_query)
            )[:10]  # Limit to 10 results
            
            results = [
                {
                    'id': vehicle.id,
                    'number': vehicle.number,
                    'make': vehicle.make,
                    'model': vehicle.model,
                    'display_text': f"{vehicle.number} - {vehicle.make} {vehicle.model}"
                }
                for vehicle in vehicles
            ]
            
            return JsonResponse({'results': results})
    
    return JsonResponse({'results': []})


# Additional utility views
@login_required
def vehicle_statistics(request):
    """
    Get vehicle statistics for dashboard
    """
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Calculate various statistics
        total_vehicles = Vehicle.objects.filter(user=request.user).count()
        
        # Vehicles by make
        makes_data = Vehicle.objects.filter(user=request.user).values('make').annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        
        # Recent activity (last 7 days)
        seven_days_ago = timezone.now() - timedelta(days=7)
        recent_activity = Vehicle.objects.filter(
            user=request.user,
            created_at__gte=seven_days_ago
        ).count()
        
        # Monthly additions for the last 6 months
        monthly_data = []
        for i in range(6):
            start_date = timezone.now().replace(day=1) - timedelta(days=30*i)
            end_date = (start_date + timedelta(days=32)).replace(day=1)
            
            count = Vehicle.objects.filter(
                user=request.user,
                created_at__gte=start_date,
                created_at__lt=end_date
            ).count()
            
            monthly_data.append({
                'month': start_date.strftime('%b %Y'),
                'count': count
            })
        
        monthly_data.reverse()
        
        stats = {
            'total_vehicles': total_vehicles,
            'makes_data': list(makes_data),
            'recent_activity': recent_activity,
            'monthly_data': monthly_data
        }
        
        return JsonResponse(stats)
    
    return JsonResponse({'error': 'Invalid request'})


@login_required
def bulk_delete_vehicles(request):
    """
    Delete multiple vehicles at once
    """
    if request.method == 'POST':
        vehicle_ids = request.POST.getlist('vehicle_ids')
        
        if vehicle_ids:
            try:
                deleted_count = Vehicle.objects.filter(
                    id__in=vehicle_ids,
                    user=request.user
                ).delete()[0]
                
                messages.success(request, f'{deleted_count} vehicles have been deleted successfully!')
            except Exception as e:
                messages.error(request, f'Error deleting vehicles: {str(e)}')
        else:
            messages.warning(request, 'No vehicles selected for deletion')
    
    return redirect('vehicles:vehicle_list')