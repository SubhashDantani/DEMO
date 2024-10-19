from django.db import models
from users.models import CustomUser
from bids.models import Bid

class Payment(models.Model):
    bid = models.OneToOneField(Bid, on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    razorpay_payment_id = models.CharField(max_length=100, null=True, blank=True)
    razorpay_order_id = models.CharField(max_length=100, null=True, blank=True)
    razorpay_signature = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default="Pending")  # Payment status (Pending, Completed, Failed)

    def __str__(self):
        return f"Payment for Bid {self.bid.id} by {self.user.username} - {self.status}"
    