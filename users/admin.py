from django.contrib import admin
from .models import CustomUser

# Register your models here.
class userDisplay(admin.ModelAdmin):
    list_display=["username"]
admin.site.register(CustomUser,userDisplay)
