from django.http import JsonResponse
from .models import Category
from django.views import View
from django.forms.models import model_to_dict
from .utils import get_stockids_by_category
from stock.utils import get_stock_info

class CategoryListView(View):
    def get(self, request):
        categories = Category.objects.all()
        data = [model_to_dict(cat) for cat in categories]
        return JsonResponse(data, safe=False)

class CategoryStockListView(View):
    def get(self, request, category_id):
        stockids = get_stockids_by_category(category_id)
        stocks = []
        for stockid in stockids:
            stock = get_stock_info(stockid)
            if stock:
                stocks.append({
                    'id': stock['id'],
                    'industry_code': stock['industry_code'],
                    'name': stock['name'],
                    'volume_power': stock['volume_power'],
                    'current_price': stock['current_price'],
                    'type': stock['type'],
                    'eq': stock['eq'],
                    'country': stock['country'],
                    'updown_rate': stock['updown_rate'],
                })
        return JsonResponse(stocks, safe=False)
