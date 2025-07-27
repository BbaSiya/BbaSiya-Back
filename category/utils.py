from .models import StockCategory

def get_stockids_by_category(category_id):
    return list(StockCategory.objects.filter(categoryid=category_id).values_list('stockid', flat=True)) 