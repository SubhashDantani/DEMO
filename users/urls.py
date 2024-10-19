from django.urls import path
from . import views

app_name = "users"

urlpatterns = [
    path('', views.login, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout, name='logout'),
    path('Forgot-password/', views.forgot_password, name='forgetpass'),
    path('OTP/', views.sendotp, name='otppage'),
    path('Set-password/', views.setpassword, name='newpassword'),
]

