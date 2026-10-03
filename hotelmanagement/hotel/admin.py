from django.contrib import admin

from .models import Booking, Category, Guest, Room


admin.site.register(Category)
admin.site.register(Room)
admin.site.register(Guest)
admin.site.register(Booking)
