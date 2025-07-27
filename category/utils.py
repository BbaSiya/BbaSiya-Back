from stock.utils import *
from .models import StockCategory

def get_stockids_by_category(category_id):
    """
    category_id에 해당하는 모든 stockid 리스트 반환
    """
    stocklist = list(StockCategory.objects.filter(categoryid=category_id).values_list('stockid', flat=True))
    renew_stockinfo(stocklist)
    
    return stocklist