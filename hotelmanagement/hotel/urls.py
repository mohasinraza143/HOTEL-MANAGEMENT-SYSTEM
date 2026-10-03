from django.urls import path

from . import admin_views, views


urlpatterns = [
    # Guest & Public Routes
    path("", views.home, name="home"),
    path("register/", views.register_user, name="register"),
    path("login/", views.login_user, name="login"),
    path("logout/", views.logout_user, name="logout"),
    path("rooms/", views.rooms, name="rooms"),
    path("rooms/<int:room_id>/", views.room_detail, name="room_detail"),
    path("booking/", views.booking, name="booking"),
    path("booking/<int:room_id>/", views.booking, name="book_room"),
    path("booking/confirmation/<int:booking_id>/", views.booking_confirmation, name="booking_confirmation"),
    path("bookings/", views.booking_history, name="booking_history"),
    path("bookings/<int:booking_id>/status/", views.update_booking_status, name="update_booking_status"),
    path("bookings/<int:booking_id>/cancel/", views.cancel_booking, name="cancel_booking"),

    # AI Feature Endpoints
    path("api/ai/chat/", views.ai_chat_api, name="ai_chat_api"),
    path("api/ai/match/", views.ai_match_api, name="ai_match_api"),

    # Admin Portal Routes (Restricted to Staff/Admin)
    path("portal/", admin_views.admin_dashboard, name="admin_dashboard"),
    path("portal/rooms/", admin_views.admin_rooms, name="admin_rooms"),
    path("portal/rooms/new/", admin_views.admin_room_create, name="admin_room_create"),
    path("portal/rooms/<int:room_id>/edit/", admin_views.admin_room_edit, name="admin_room_edit"),
    path("portal/rooms/<int:room_id>/delete/", admin_views.admin_room_delete, name="admin_room_delete"),
    path("portal/rooms/<int:room_id>/toggle/", admin_views.admin_room_toggle, name="admin_room_toggle"),
    path("portal/bookings/", admin_views.admin_bookings, name="admin_bookings"),
    path("portal/bookings/<int:booking_id>/status/", admin_views.admin_booking_status, name="admin_booking_status"),
    path("portal/categories/", admin_views.admin_categories, name="admin_categories"),
    path("portal/categories/<int:category_id>/delete/", admin_views.admin_category_delete, name="admin_category_delete"),
    path("portal/guests/", admin_views.admin_guests, name="admin_guests"),
    path("portal/staff/new/", admin_views.admin_staff_create, name="admin_staff_create"),
    path("portal/users/<int:user_id>/toggle-staff/", admin_views.admin_user_toggle_staff, name="admin_user_toggle_staff"),
    path("portal/ai/", admin_views.admin_ai_view, name="admin_ai_view"),
]
