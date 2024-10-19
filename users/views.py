from django.shortcuts import render, redirect
from django.contrib import messages
from .models import CustomUser
from django.core.mail import send_mail
import random
import string
def login(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        user = CustomUser.objects.filter(email=email).first()
        try:
            if user and user.check_password(password):
                request.session['user_id'] = user.id
                request.session['email'] = user.email
                messages.success(request, 'Logged in successfully.')
                return redirect('bids:index')
            else:
                messages.error(request, 'Invalid credentials.')
        except CustomUser.DoesNotExist:
            messages.error(request, 'User does not exist.')
    return render(request, 'login.html')
from django.contrib.auth.hashers import make_password
def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        print("999999999",email)
        try:
            user = CustomUser.objects.get(email=email)
            print("999999999",user)

            if user:
                characters =  string.digits 
                OTP = ''.join(random.choice(characters) for i in range(6))
                request.session['otp']=OTP
                request.session['email']=email
                send_mail(
                    'OTP  mail from Bidding System',
                    f'Dear {user.username},\n OTP is:  {OTP}',
                    'akshaydantani96@gmail.com',  # TODO: Update this with your email id
                    [email],  # TODO: Update this with the recipient's email id
                    fail_silently=False,
                )
                messages.success(request, 'OTP is sent to your registered email id.')
                return redirect('users:otppage')
        except CustomUser.DoesNotExist:
            messages.error(request, 'Invalid email. The email is not registered.')
    return render(request, 'Forgot.html')

def sendotp(request):
    if  request.session['otp']:
        if request.method == 'POST':
            otp = request.POST.get('otp')
            if request.session['otp']==otp:              
                    messages.success(request, 'OTP is varified.')
                    del request.session['otp']
                    return redirect('users:newpassword')
            else:
                messages.error(request, 'Invalid OTP.')
                return redirect('users:otppage')
        return render(request, 'OTP.html')

def setpassword(request):
    if  request.session['email']:
        user = CustomUser.objects.get(email=request.session['email'])

        if request.method == 'POST':
            new_password = request.POST.get('password')
            user.password=make_password(new_password)
            user.save()             
            messages.success(request, 'New Password Set Sucessfully.')
            del request.session['email']
            return redirect('users:login')
        return render(request, 'newpassword.html')

def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        contact = request.POST['contact']
        image = request.FILES.get('image')

        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists.')
        elif CustomUser.objects.filter(contact=contact).exists():
            messages.error(request, 'Contact already exists.')
        else:
            user = CustomUser(username=username, email=email, password=password, contact=contact, image=image) 
            user.save()
            messages.success(request, 'Registration successful.')
            return redirect('users:login')
    return render(request, 'register.html')

def logout(request):
    request.session.flush()
    messages.success(request, 'Logged out successfully!')
    return redirect('users:login')
