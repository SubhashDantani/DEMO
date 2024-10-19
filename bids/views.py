from django.utils import timezone
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from users.models import CustomUser
from .models import Product, Bid
from django.db.models import Q, Count
from django.utils.timezone import localtime
from django.contrib.auth.hashers import make_password
from datetime import timedelta

def index(request):
    user_id = request.session.get('user_id')
    now = timezone.now()
    if not user_id:
        messages.error(request, 'You need to log in first.')
        return redirect('users:login')
    try:
        products = Product.objects.filter(
            auction_end_time__gt=now  # Exclude products with ended auctions
        )
        return render(request, 'index.html',{'products': products})
    except Exception as e:
        messages.error(request, f"Error loading homepage: {str(e)}")
        return render(request, 'index.html')
    
def profile(request):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, 'You need to log in first.')
        return redirect('users:login')

    user = get_object_or_404(CustomUser, id=user_id)
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        image = request.FILES.get('image')
        contact = request.POST.get('contact')

        if username:
            user.username = username
        if email:
            user.email = email
        if contact:
            user.contact = contact
        if image:
            user.image.delete()
            user.image = image

        user.save()
        messages.success(request, 'Profile updated successfully.')
        return redirect('bids:profile')
    
    return render(request, 'profile.html', {'user': user})

def change_password(request):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, 'You need to log in first.')
        return redirect('users:login')

    user = get_object_or_404(CustomUser, id=user_id)

    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        if user.check_password(old_password):
            if new_password == confirm_password:
                user.password = make_password(new_password)  # Hash the new password
                user.save()
                messages.success(request, 'Password changed successfully.')
                return redirect('bids:profile')
            else:
                messages.error(request, 'New passwords do not match.')
        else:
            messages.error(request, 'Old password is incorrect.')

    return render(request, "change_password.html")

def product_list(request):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, 'You need to log in first.')
        return redirect('users:login')

    search_query = request.GET.get('search', '')
    sort_by = request.GET.get('sort_by', 'name')  # Default to sorting by name

    # Get current time for filtering out expired auctions
    now = timezone.now()

    try:
        # Filter out products whose auction has ended
        products = Product.objects.filter(
            Q(name__icontains=search_query) | Q(description__icontains=search_query),
            auction_end_time__gt=now  # Exclude products with ended auctions
        )

        # Sorting logic
        if sort_by == 'current_price_lh':
            products = products.order_by('starting_price')  # Low to High
        elif sort_by == 'current_price_hl':
            products = products.order_by('-starting_price')  # High to Low
        elif sort_by == 'popularity':
            # Sort by popularity (number of bids on the product)
            products = products.annotate(num_bids=Count('bid')).order_by('-num_bids')
        else:
            products = products.order_by(sort_by)  # Default sorting

    except Exception as e:
        messages.error(request, f"Error fetching products: {str(e)}")
        products = []

    return render(request, 'product_list.html', {'products': products})

def product_detail(request, product_id):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, 'You need to log in first.')
        return redirect('users:login')
    
    # Get the product and relevant bids
    product = get_object_or_404(Product, pk=product_id)
    bids = Bid.objects.filter(product=product).order_by('-bid_amount')[:3]
    
    # Get auction end time as datetime object for comparison
    auction_end_time = localtime(product.auction_end_time)
    auction_end_time_iso = auction_end_time.isoformat()  # For JavaScript
    now = timezone.now()

    # Handle bid submission
    if request.method == 'POST':
        bid_amount = request.POST.get('bid_amount')

        try:
            user = CustomUser.objects.get(pk=user_id)
            bid_amount = float(bid_amount)

            # Check if auction has ended using datetime objects
            if now > auction_end_time:
                messages.error(request, "You can't bid now, the auction has ended.")
                return redirect('bids:product_detail', product_id=product.id)

            # Ensure the bid amount is higher than the current price
            if bid_amount <= product.current_price:
                messages.error(request, 'Bid must be higher than the current price.')
            else:
                # Check if the user has already placed a bid on this product
                existing_bid = Bid.objects.filter(product=product, user=user).first()

                if existing_bid:
                    # Update the existing bid with the new amount
                    existing_bid.bid_amount = bid_amount
                    existing_bid.save()
                    messages.success(request, 'Your bid has been updated!')
                else:
                    # Create a new bid entry if no previous bid exists
                    Bid.objects.create(product=product, user=user, bid_amount=bid_amount)
                    messages.success(request, 'Bid placed successfully!')

                # Update the current price of the product
                product.current_price = bid_amount
                product.save()
                
                return redirect('bids:product_detail', product_id=product.id)

        except ValueError:
            messages.error(request, 'Invalid bid amount.')

    return render(request, 'product_detail.html', {
        'product': product, 
        'bids': bids, 
        'auction_end_time': auction_end_time_iso,  # Pass ISO formatted string for JavaScript
    })

def bid_confirmation(request):
    # Check if the user is logged in
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, 'You need to log in first.')
        return redirect('users:login')
    
    search_query = request.GET.get('search', '')

    # Call the function to assign ownership of products after the auction ends
    assign_owners_after_auction_ends()  # Assign owners where auctions have ended

    # Get all bids for the logged-in user
    if search_query:
        bids = Bid.objects.filter(user_id=user_id).filter(Q(product__name__icontains=search_query)).select_related('product').prefetch_related('payment')    
    else:
        bids = Bid.objects.filter(user_id=user_id).select_related('product').prefetch_related('payment')

    # Get the current time to check if the auction has ended
    now = timezone.now()

    # Process each bid
    for bid in bids:
        auction_end_time = bid.product.auction_end_time
        payment_due_time = auction_end_time + timedelta(hours=48)  # 48 hours after auction ends

        # Calculate if payment due time has passed
        bid.payment_due_expired = now > payment_due_time

        # Check if the payment is overdue
        if bid.is_payment_due() and bid.payment_due_expired:
            # Only remove ownership if the user is the current owner and overdue payment
            if bid.product.owner == bid.user:
                bid.product.owner = None  # Remove ownership due to non-payment
                bid.product.save()

    return render(request, 'bid_confirmation.html', {
        'bids': bids,
        'now': now
    })

def assign_owners_after_auction_ends():
    """
    Assigns the highest bidder as the owner for all products whose auctions have ended,
    only if they are eligible for ownership.
    """
    now = timezone.now()
    products = Product.objects.filter(auction_end_time__lt=now, owner__isnull=True)  # Products without an owner and with ended auctions
    for product in products:
        product.assign_owner_to_highest_bidder()  # Assign the highest bidder as the owner (if eligible)

def dashboard(request):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, 'You need to log in first.')
        return redirect('users:login')
    
    user1 = CustomUser.objects.get(pk=user_id)
    active_bids = Bid.objects.filter(user=user1, product__auction_end_time__gte=timezone.now())
    past_bids = Bid.objects.filter(user=user1, product__auction_end_time__lt=timezone.now())
    user = get_object_or_404(CustomUser, id=user_id)
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        image = request.FILES.get('image')
        contact = request.POST.get('contact')

        if username:
            user.username = username
        if email:
            user.email = email
        if contact:
            user.contact = contact
        if image:
            user.image.delete()
            user.image = image

        user.save()
        messages.success(request, 'Profile updated successfully.')
        return redirect('bids:dashboard')
    return render(request, 'dashboard.html', {'user': user,'active_bids': active_bids, 'past_bids': past_bids})

def auction_details(request):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, 'You need to log in first.')
        return redirect('users:login')
    try:
        return render(request, 'auction_details.html')
    except Exception as e:
        messages.error(request, f"Error loading auction details: {str(e)}")
        return render(request, 'auction_details.html')

