from django.db import models

class MyStock(models.Model):
    id = models.AutoField(primary_key=True)
    stockid = models.CharField(max_length=10)
    userid = models.IntegerField()
    cnt = models.IntegerField(null=True)
    average_cnt = models.IntegerField(null=True)
    date = models.DateTimeField(null=True)

    class Meta:
        db_table = 'mystock'

