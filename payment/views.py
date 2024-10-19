import razorpay
from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.csrf import csrf_exempt
from users.models import CustomUser
from .models import Payment, Bid
from django.contrib import messages
import logging

logger = logging.getLogger(__name__)

# Razorpay Client Setup
razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

def initiate_payment(request, bid_id):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, 'You need to log in first.')
        return redirect('users:login')
    
    # Get the logged-in user
    user = get_object_or_404(CustomUser, pk=user_id)
    
    # Get the bid object
    bid = get_object_or_404(Bid, pk=bid_id)
    
    # Check if a payment already exists for this bid
    payment = Payment.objects.filter(bid=bid).first()
    
    if payment:
        # If a payment already exists, notify the user
        # messages.warning(request, 'Payment has already been initiated for this bid.')
        pass
    else:
        # Create a new payment entry if none exists
        amount = float(bid.bid_amount) * 100  # Razorpay accepts amount in paise
        payment = Payment.objects.create(bid=bid, user=user, amount=bid.bid_amount)

        # Create a Razorpay Order
        razorpay_order = razorpay_client.order.create({
            "amount": amount,  # In paise
            "currency": "INR",
            "payment_capture": "1"  # Capture the payment automatically
        })
        
        # Store Razorpay order details in the payment object
        payment.razorpay_order_id = razorpay_order['id']
        payment.save()

    return render(request, 'payment.html', {
        'bid': bid,
        'payment': payment,
        'razorpay_order_id': payment.razorpay_order_id,
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
        'amount': float(payment.amount) * 100  # Razorpay expects the amount in paise
    })


@csrf_exempt
def payment_success(request):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, 'You need to log in first.')
        return redirect('users:login')

    if request.method == "POST":
        try:
            # Get Razorpay details from the POST request
            razorpay_payment_id = request.POST.get('razorpay_payment_id')
            razorpay_order_id = request.POST.get('razorpay_order_id')
            razorpay_signature = request.POST.get('razorpay_signature')
            bid_id = request.POST.get('bid_id') 

            # Find the corresponding payment and bid in the database
            payment = Payment.objects.get(razorpay_order_id=razorpay_order_id)
            payment.razorpay_payment_id = razorpay_payment_id
            payment.razorpay_signature = razorpay_signature
            payment.status = "Completed"
            payment.save()

            # Find the corresponding bid and update its status
            bid = Bid.objects.get(id=bid_id)
            bid.payment_completed = True
            bid.save()

            messages.success(request, "Payment successful! Thank you for your purchase.")
            return redirect('payment:success_page')

        except Payment.DoesNotExist:
            messages.error(request, "Payment record not found.")
            return redirect('payment:failure_page')
        except Bid.DoesNotExist:
            messages.error(request, "Bid record not found.")
            return redirect('payment:failure_page')
        except Exception as e:
            # logger.error(f"Payment failed: {str(e)}")
            messages.error(request, f"Payment failed: {str(e)}")
            return redirect('payment:failure_page')

def success_page(request):
    return render(request, 'success.html')

def failure_page(request):
    return render(request, 'failure.html')
