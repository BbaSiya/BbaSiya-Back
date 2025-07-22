from django.db import models
from stock.models import Stock

# Create your models here.

class Category(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'category'

class StockCategory(models.Model):
    stock_category_id = models.AutoField(primary_key=True)
    stockid = models.CharField(max_length=10)
    categoryid = models.IntegerField()

    class Meta:
        db_table = 'stock_category' 
