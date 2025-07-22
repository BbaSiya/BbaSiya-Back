from django.http import JsonResponse
from .models import Category
from django.views import View
from django.forms.models import model_to_dict

class CategoryListView(View):
    def get(self, request):
        categories = Category.objects.all()
        data = [model_to_dict(cat) for cat in categories]
        return JsonResponse(data, safe=False)
