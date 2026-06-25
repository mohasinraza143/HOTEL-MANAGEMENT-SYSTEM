from django.contrib.auth.models import User
from django.db import models


BOOKING_STATUS_CHOICES = [
    ("Reserved", "Reserved"),
    ("Checked-in", "Checked-in"),
    ("Checked-out", "Checked-out"),
]


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Room(models.Model):
    room_number = models.CharField(max_length=20, unique=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="rooms")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    image = models.TextField(help_text="Use a URL or a data URI for demo room images.")
    availability = models.BooleanField(default=True)

    def __str__(self):
        return f"Room {self.room_number}"


class Guest(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, related_name="guest_profile")
    name = models.CharField(max_length=120)
    phone = models.CharField(max_length=20)

    def __str__(self):
        return self.name


class Booking(models.Model):
    guest = models.ForeignKey(Guest, on_delete=models.CASCADE, related_name="bookings")
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="bookings")
    check_in = models.DateField()
    check_out = models.DateField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=BOOKING_STATUS_CHOICES, default="Reserved")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Booking {self.id} - {self.guest.name}"
