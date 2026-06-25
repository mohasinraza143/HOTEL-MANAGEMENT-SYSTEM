from django.urls import path

from . import views


urlpatterns = [
    path("", views.home, name="home"),
    path("register/", views.register_user, name="register"),
    path("login/", views.login_user, name="login"),
    path("logout/", views.logout_user, name="logout"),
    path("rooms/", views.rooms, name="rooms"),
    path("rooms/<int:room_id>/", views.room_detail, name="room_detail"),
    path("booking/", views.booking, name="booking"),
    path("booking/<int:room_id>/", views.booking, name="book_room"),
    path(
        "booking/confirmation/<int:booking_id>/",
        views.booking_confirmation,
        name="booking_confirmation",
    ),
    path("bookings/", views.booking_history, name="booking_history"),
    path(
        "bookings/<int:booking_id>/status/",
        views.update_booking_status,
        name="update_booking_status",
    ),
]
