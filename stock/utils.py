from .models import Stock, ClosingPriceLog

def get_stock_info(stockid):
    """
    stockid에 해당하는 Stock 정보와 가장 최신 ClosingPriceLog의 updown_rate를 dict로 반환 (없으면 None)
    """
    try:
        stock = Stock.objects.get(id=stockid)
        latest_log = ClosingPriceLog.objects.filter(stockid=stockid).order_by('-date').first()
        updown_rate = latest_log.updown_rate if latest_log else None
        return {
            'id': stock.id,
            'industry_code': stock.industry_code,
            'name': stock.name,
            'volume_power': stock.volume_power,
            'current_price': stock.current_price,
            'type': stock.type,
            'eq': stock.eq,
            'country': stock.country,
            'latest_updown_rate': updown_rate,
        }
    except Stock.DoesNotExist:
        return None 