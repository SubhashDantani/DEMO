from django.urls import path
from . import views

app_name = "bids"

urlpatterns = [
    path('', views.index, name='index'),
    path('profile/', views.profile, name='profile'),
    path('change_password/', views.change_password, name='change_password'),
    path('products/', views.product_list, name='product_list'),
    path('products/<int:product_id>/', views.product_detail, name='product_detail'),
    path('bid-confirmation/', views.bid_confirmation, name='bid_confirmation'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('auction_details/', views.auction_details, name='auction_details'),
]
