from django.contrib import admin
from .models import Payment

# Register your models here.
class paymentDisplay(admin.ModelAdmin):
    list_display=["user"]
admin.site.register(Payment, paymentDisplay)
