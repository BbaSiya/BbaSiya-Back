from django.urls import path
from .views import CategoryListView, CategoryStockListView

urlpatterns = [
    path('category/', CategoryListView.as_view(), name='category-list'),
    path('category/category_id=<int:category_id>/', CategoryStockListView.as_view(), name='category-stock-list'),
] 