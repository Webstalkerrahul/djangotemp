from billing.models import Invoice,Company  
from django.db.models import Sum, Value, DecimalField
from django.db.models.functions import Coalesce

def get_invoice_data(request):
    company = Company.objects.filter(user=request.user).first()
    invoice_data = Invoice.objects.filter(company=company).select_related(
        'vendor', 'plant', 'vehicle', 'product', 'company'
    ).order_by('-created_at')

    grand_total = invoice_data.aggregate(
        total=Coalesce(
            Sum('net_amount'),          # add up every net_amount
            Value(0),                   # fallback if there are no rows
            output_field=DecimalField() # make sure the result is Decimal
        )
    )['total']
    return invoice_data, grand_total
