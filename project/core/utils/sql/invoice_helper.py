from billing.models import Invoice,Company  

def get_invoice_data(request):
    company = Company.objects.filter(user=request.user).first()
    invoice_data = Invoice.objects.filter(company=company).select_related(
        'vendor', 'plant', 'vehicle', 'product', 'company'
    ).order_by('-created_at')
    return invoice_data