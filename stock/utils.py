from .models import Stock, ClosingPriceLog, Industry

def get_stock_info(stockid):
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

def get_industry_name_by_stockid(stockid):
    try:
        stock = Stock.objects.get(id=stockid)
        industry = Industry.objects.get(industry_code=stock.industry_code)
        return industry.industry_name
    except (Stock.DoesNotExist, Industry.DoesNotExist):
        return None 