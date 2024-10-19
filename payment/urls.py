from django.urls import path
from . import views

app_name = 'payment'

urlpatterns = [
    path('initiate-payment/<int:bid_id>/', views.initiate_payment, name='initiate_payment'),
    path('payment-success/', views.payment_success, name='payment_success'),
    path('success/', views.success_page, name='success_page'),
    path('failure/', views.failure_page, name='failure_page'),
]
