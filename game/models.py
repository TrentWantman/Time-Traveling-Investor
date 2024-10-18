from django.db import models
from django.contrib.auth.models import User

class StockSelection(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    stock_symbol = models.CharField(max_length=10)
    purchase_date = models.DateField()
    quantity = models.PositiveIntegerField()
    purchase_price = models.FloatField()
    future_price = models.FloatField(null=True, blank=True)
    profit_loss = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.stock_symbol}"