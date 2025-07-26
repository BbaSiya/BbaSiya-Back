from stock.utils import *
from .models import StockCategory

def get_stockids_by_category(category_id):
    """
    category_id에 해당하는 모든 stockid 리스트 반환
    """
    stocklist = list(StockCategory.objects.filter(category_id=category_id).values_list('stockid', flat=True))
    renew_stockinfo(stocklist)
    
    return list(StockCategory.objects.filter(categoryid=category_id).values_list('stockid', flat=True)) 

'''
가져와서
현재가 덮어쓰고 조회하기
조회하고 갈아끼우고 덮어쓰고 반환하기
'''