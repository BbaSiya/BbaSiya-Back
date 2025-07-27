from django.db import models

# Create your models here.

class Stock(models.Model):
    id = models.CharField(max_length=10, primary_key=True)
    industry_code = models.CharField(max_length=10)
    name = models.CharField(max_length=40)
    volume_power = models.FloatField(null=True)
    current_price = models.FloatField(null=True)
    type = models.CharField(max_length=10, null=True)
    eq = models.IntegerField(null=True)
    country = models.CharField(max_length=2, null=True)
    updown_rate = models.FloatField(null=True)

    class Meta:
        db_table = 'stock'

class ClosingPriceLog(models.Model):
    id = models.AutoField(primary_key=True)
    stockid = models.CharField(max_length=10)
    date = models.DateTimeField()
    closing_price = models.FloatField()
    updown_rate = models.FloatField()

    class Meta:
        db_table = 'closing_price_log'

class Industry(models.Model):
    industry_code = models.CharField(max_length=10, primary_key=True)
    industry_name = models.CharField(max_length=10)

    class Meta:
        db_table = 'industry'
