from django.db import models
from users.models import CustomUser
from django.utils import timezone
from datetime import timedelta

class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    starting_price = models.DecimalField(max_digits=10, decimal_places=2)
    current_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    auction_start_time = models.DateTimeField()
    auction_end_time = models.DateTimeField()
    image = models.ImageField(upload_to='product_images/', null=True, blank=True)
    video = models.FileField(upload_to='product_videos/', null=True, blank=True)
    owner = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True) 

    def save(self, *args, **kwargs):
        # Set current_price to starting_price only if current_price is not set
        if self.pk is None and self.current_price is None:
            self.current_price = self.starting_price
        super().save(*args, **kwargs)

    def assign_owner_to_highest_bidder(self):
        """
        This method assigns the product to the highest bidder after the auction ends,
        but only if the highest bid is eligible for ownership (i.e., payment done or within 48 hours).
        """
        highest_bid = Bid.objects.filter(product=self).order_by('-bid_amount').first()  # Get the highest bid
        if highest_bid and highest_bid.is_eligible_for_ownership():
            self.owner = highest_bid.user  # Assign the highest bidder as the owner
            self.save()

    def __str__(self):
        return self.name
    
class Bid(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    bid_amount = models.DecimalField(max_digits=10, decimal_places=2)
    bid_time = models.DateTimeField(auto_now_add=True)
    payment_completed = models.BooleanField(default=False)  # Track payment status

    def is_eligible_for_ownership(self):
        """ Check if the bid is still eligible for ownership (i.e., within 48 hours after auction ends). """
        auction_end_time = self.product.auction_end_time
        # If payment is completed, or we are still within the 48-hour window after auction end
        return self.payment_completed or timezone.now() <= auction_end_time + timedelta(hours=48)

    def is_payment_due(self):
        # Check if the auction has ended
        if self.product.auction_end_time + timedelta(hours=48) < timezone.now():
            return True
        return False

    def __str__(self):
        return f"{self.user} - {self.product.name} - {self.bid_amount}"
    
    class Meta:
        ordering = ['-bid_time']  # Show latest bids first
