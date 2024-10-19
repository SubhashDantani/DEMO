from django.contrib import admin
from .models import Bid, Product

# Register your models here.
class productDisplay(admin.ModelAdmin):
    readonly_fields = ['current_price']
    list_display=["name"]
admin.site.register(Product, productDisplay)

class bidDisplay(admin.ModelAdmin):
    list_display=["product"]
admin.site.register(Bid, bidDisplay)
