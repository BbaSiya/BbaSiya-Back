from django.urls import path
from .views import StockSimilarityView, UserCategoryRecommendationView

urlpatterns = [
    path('stock/stock_id=<str:stock_id>&user_id=<int:user_id>/', StockSimilarityView.as_view(), name='stock-similarity'),
    path('topPic/', UserCategoryRecommendationView.as_view(), name='user-category-recommendation'),
] 