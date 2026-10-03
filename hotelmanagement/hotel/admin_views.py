from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db.models import Avg, Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render

from .ai_service import get_admin_ai_insights
from .models import BOOKING_STATUS_CHOICES, Booking, Category, Guest, Room


def staff_check(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


@login_required(login_url="login")
@user_passes_test(staff_check, login_url="login")
def admin_dashboard(request):
    total_rooms = Room.objects.count()
    available_rooms = Room.objects.filter(availability=True).count()
    occupied_rooms = total_rooms - available_rooms
    occupancy_pct = round((occupied_rooms / total_rooms * 100), 1) if total_rooms else 0

    all_bookings = Booking.objects.select_related("guest", "room", "room__category")
    total_bookings = all_bookings.count()
    active_bookings = all_bookings.filter(status__in=["Reserved", "Checked-in"]).count()
    completed_bookings = all_bookings.filter(status="Checked-out").count()
    cancelled_bookings = all_bookings.filter(status="Cancelled").count()

    total_revenue = (
        all_bookings.exclude(status="Cancelled").aggregate(Sum("total_price"))["total_price__sum"]
        or Decimal("0.00")
    )
    avg_price = Room.objects.aggregate(Avg("price"))["price__avg"] or Decimal("0.00")

    recent_bookings = all_bookings.order_by("-created_at")[:6]
    ai_insights = get_admin_ai_insights()

    context = {
        "total_rooms": total_rooms,
        "available_rooms": available_rooms,
        "occupied_rooms": occupied_rooms,
        "occupancy_pct": occupancy_pct,
        "total_bookings": total_bookings,
        "active_bookings": active_bookings,
        "completed_bookings": completed_bookings,
        "cancelled_bookings": cancelled_bookings,
        "total_revenue": total_revenue,
        "avg_price": avg_price,
        "recent_bookings": recent_bookings,
        "ai_insights": ai_insights,
    }
    return render(request, "hotel/admin/dashboard.html", context)


@login_required(login_url="login")
@user_passes_test(staff_check, login_url="login")
def admin_rooms(request):
    category_id = request.GET.get("category", "")
    availability = request.GET.get("availability", "")
    search_q = request.GET.get("search", "").strip()

    rooms_qs = Room.objects.select_related("category").all().order_by("room_number")

    if category_id:
        rooms_qs = rooms_qs.filter(category_id=category_id)
    if availability == "available":
        rooms_qs = rooms_qs.filter(availability=True)
    elif availability == "unavailable":
        rooms_qs = rooms_qs.filter(availability=False)
    if search_q:
        rooms_qs = rooms_qs.filter(
            Q(room_number__icontains=search_q)
            | Q(category__name__icontains=search_q)
            | Q(description__icontains=search_q)
        )

    categories = Category.objects.all().order_by("name")

    context = {
        "rooms": rooms_qs,
        "categories": categories,
        "selected_category": category_id,
        "selected_availability": availability,
        "search_q": search_q,
    }
    return render(request, "hotel/admin/rooms.html", context)


@login_required(login_url="login")
@user_passes_test(staff_check, login_url="login")
def admin_room_create(request):
    categories = Category.objects.all().order_by("name")
    if request.method == "POST":
        room_number = request.POST.get("room_number", "").strip().upper()
        category_id = request.POST.get("category", "")
        price = request.POST.get("price", "").strip()
        description = request.POST.get("description", "").strip()
        image = request.POST.get("image", "").strip()
        availability = request.POST.get("availability") == "on"

        if not all([room_number, category_id, price, description]):
            messages.error(request, "Please fill in all required room details.")
        elif Room.objects.filter(room_number=room_number).exists():
            messages.error(request, f"Room {room_number} already exists! Use a different room number.")
        else:
            category = get_object_or_404(Category, id=category_id)
            if not image:
                image = (
                    "https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=800&q=80"
                )
            Room.objects.create(
                room_number=room_number,
                category=category,
                price=Decimal(price),
                description=description,
                image=image,
                availability=availability,
            )
            messages.success(request, f"Room {room_number} created successfully!")
            return redirect("admin_rooms")

    return render(request, "hotel/admin/room_form.html", {"categories": categories, "action": "Create"})


@login_required(login_url="login")
@user_passes_test(staff_check, login_url="login")
def admin_room_edit(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    categories = Category.objects.all().order_by("name")

    if request.method == "POST":
        room_number = request.POST.get("room_number", "").strip().upper()
        category_id = request.POST.get("category", "")
        price = request.POST.get("price", "").strip()
        description = request.POST.get("description", "").strip()
        image = request.POST.get("image", "").strip()
        availability = request.POST.get("availability") == "on"

        if not all([room_number, category_id, price, description]):
            messages.error(request, "Please fill in all required room details.")
        elif Room.objects.filter(room_number=room_number).exclude(id=room.id).exists():
            messages.error(request, f"Room {room_number} is already in use by another room.")
        else:
            category = get_object_or_404(Category, id=category_id)
            room.room_number = room_number
            room.category = category
            room.price = Decimal(price)
            room.description = description
            if image:
                room.image = image
            room.availability = availability
            room.save()
            messages.success(request, f"Room {room_number} updated successfully!")
            return redirect("admin_rooms")

    return render(
        request,
        "hotel/admin/room_form.html",
        {"categories": categories, "room": room, "action": "Edit"},
    )


@login_required(login_url="login")
@user_passes_test(staff_check, login_url="login")
def admin_room_delete(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    if request.method == "POST":
        r_num = room.room_number
        room.delete()
        messages.success(request, f"Room {r_num} was deleted.")
        return redirect("admin_rooms")
    return render(request, "hotel/admin/room_confirm_delete.html", {"room": room})


@login_required(login_url="login")
@user_passes_test(staff_check, login_url="login")
def admin_room_toggle(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    room.availability = not room.availability
    room.save()
    status_label = "Available" if room.availability else "Unavailable"
    messages.success(request, f"Room {room.room_number} is now marked as {status_label}.")
    return redirect("admin_rooms")


@login_required(login_url="login")
@user_passes_test(staff_check, login_url="login")
def admin_bookings(request):
    status_filter = request.GET.get("status", "")
    search_q = request.GET.get("search", "").strip()

    bookings_qs = Booking.objects.select_related("guest", "room", "room__category").all().order_by("-created_at")

    if status_filter:
        bookings_qs = bookings_qs.filter(status=status_filter)
    if search_q:
        bookings_qs = bookings_qs.filter(
            Q(guest__name__icontains=search_q)
            | Q(room__room_number__icontains=search_q)
            | Q(id__icontains=search_q)
            | Q(guest__phone__icontains=search_q)
        )

    context = {
        "bookings": bookings_qs,
        "status_choices": BOOKING_STATUS_CHOICES,
        "selected_status": status_filter,
        "search_q": search_q,
    }
    return render(request, "hotel/admin/bookings.html", context)


@login_required(login_url="login")
@user_passes_test(staff_check, login_url="login")
def admin_booking_status(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    if request.method == "POST":
        new_status = request.POST.get("status", "")
        valid_statuses = [choice[0] for choice in BOOKING_STATUS_CHOICES]
        if new_status in valid_statuses:
            booking.status = new_status
            booking.save()
            messages.success(request, f"Booking #{booking.id} status updated to '{new_status}'.")
        else:
            messages.error(request, "Invalid booking status.")
    return redirect(request.META.get("HTTP_REFERER", "admin_bookings"))


@login_required(login_url="login")
@user_passes_test(staff_check, login_url="login")
def admin_categories(request):
    categories = Category.objects.annotate(room_count=Count("rooms")).order_by("name")

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        if not name:
            messages.error(request, "Category name cannot be empty.")
        elif Category.objects.filter(name__iexact=name).exists():
            messages.error(request, f"Category '{name}' already exists.")
        else:
            Category.objects.create(name=name)
            messages.success(request, f"Category '{name}' created successfully!")
            return redirect("admin_categories")

    return render(request, "hotel/admin/categories.html", {"categories": categories})


@login_required(login_url="login")
@user_passes_test(staff_check, login_url="login")
def admin_category_delete(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if request.method == "POST":
        if category.rooms.exists():
            messages.error(request, f"Cannot delete '{category.name}' because it contains {category.rooms.count()} room(s). Reassign or delete rooms first.")
        else:
            cat_name = category.name
            category.delete()
            messages.success(request, f"Category '{cat_name}' deleted.")
        return redirect("admin_categories")
    return redirect("admin_categories")


@login_required(login_url="login")
@user_passes_test(staff_check, login_url="login")
def admin_guests(request):
    search_q = request.GET.get("search", "").strip()
    guests_qs = Guest.objects.select_related("user").annotate(
        booking_count=Count("bookings"),
        total_spent=Sum("bookings__total_price"),
    ).order_by("-id")

    if search_q:
        guests_qs = guests_qs.filter(
            Q(name__icontains=search_q)
            | Q(phone__icontains=search_q)
            | Q(user__email__icontains=search_q)
            | Q(user__username__icontains=search_q)
        )

    return render(request, "hotel/admin/guests.html", {"guests": guests_qs, "search_q": search_q})


@login_required(login_url="login")
@user_passes_test(staff_check, login_url="login")
def admin_ai_view(request):
    ai_insights = get_admin_ai_insights()
    room_performance = Room.objects.annotate(
        booking_count=Count("bookings"),
        revenue=Sum("bookings__total_price"),
    ).order_by("-booking_count")[:10]

    return render(
        request,
        "hotel/admin/ai_insights.html",
        {"ai_insights": ai_insights, "room_performance": room_performance},
    )
