import json
from datetime import datetime
from decimal import Decimal
from urllib.parse import quote

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt

from .ai_service import ask_concierge, match_smart_rooms
from .models import BOOKING_STATUS_CHOICES, Booking, Category, Guest, Room


CATEGORY_DATA = [
    {
        "name": "Standard Room",
        "tagline": "Comfortable essentials for everyday hotel stays.",
        "accent": "#2563eb",
        "price": Decimal("129.00"),
        "description": "A clean and cozy room with all the basics needed for a smooth and affordable stay.",
    },
    {
        "name": "Deluxe Room",
        "tagline": "Upgraded comfort with stylish modern finishes.",
        "accent": "#059669",
        "price": Decimal("169.00"),
        "description": "A refined room with extra space, premium decor, and a polished hotel atmosphere.",
    },
    {
        "name": "Superior Room",
        "tagline": "Balanced luxury for guests who want more room to relax.",
        "accent": "#7c3aed",
        "price": Decimal("189.00"),
        "description": "A bright, spacious room offering an elevated stay experience with elegant details.",
    },
    {
        "name": "Executive Room",
        "tagline": "Premium accommodation for business and luxury travelers.",
        "accent": "#ea580c",
        "price": Decimal("229.00"),
        "description": "An upscale room with executive styling, workspace comfort, and premium guest amenities.",
    },
    {
        "name": "Suite",
        "tagline": "Elegant suite living with generous space and luxury comfort.",
        "accent": "#db2777",
        "price": Decimal("289.00"),
        "description": "A premium suite with lounge seating, elevated interiors, and a high-end hotel feel.",
    },
    {
        "name": "Family Room",
        "tagline": "Designed for group comfort and relaxed family travel.",
        "accent": "#0891b2",
        "price": Decimal("249.00"),
        "description": "A larger room with practical layout options that work well for families and small groups.",
    },
    {
        "name": "Presidential Suite",
        "tagline": "Signature luxury with the most exclusive stay experience.",
        "accent": "#0f766e",
        "price": Decimal("499.00"),
        "description": "The most luxurious suite in the hotel, offering statement design, privacy, and premium prestige.",
    },
]


ROOM_DATA = [
    {
        "room_number": "SR-101",
        "category": "Standard Room",
        "price": Decimal("129.00"),
        "availability": True,
        "title": "City Standard Stay",
        "image": "https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=1000&q=80",
        "description": "A clean and cozy room with warm ambient lighting, essential modern furniture, and a restful layout.",
    },
    {
        "room_number": "DR-204",
        "category": "Deluxe Room",
        "price": Decimal("169.00"),
        "availability": True,
        "title": "Golden Deluxe Retreat",
        "image": "https://images.unsplash.com/photo-1618773928121-c32242e63f39?auto=format&fit=crop&w=1000&q=80",
        "description": "A stylish upgraded room with polished decor, plush king bedding, and a welcoming boutique hotel feel.",
    },
    {
        "room_number": "SUP-118",
        "category": "Superior Room",
        "price": Decimal("189.00"),
        "availability": True,
        "title": "Skyline Superior Room",
        "image": "https://images.unsplash.com/photo-1566665797739-1674de7a421a?auto=format&fit=crop&w=1000&q=80",
        "description": "A spacious room with elevated comfort, elegant textures, panoramic skyline window, and calm mood.",
    },
    {
        "room_number": "EX-330",
        "category": "Executive Room",
        "price": Decimal("229.00"),
        "availability": True,
        "title": "Executive Horizon",
        "image": "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=1000&q=80",
        "description": "A premium executive room with ergonomic workstation, high-speed Wi-Fi, and luxury business-travel design.",
    },
    {
        "room_number": "SU-410",
        "category": "Suite",
        "price": Decimal("289.00"),
        "availability": False,
        "title": "Royal Lounge Suite",
        "image": "https://images.unsplash.com/photo-1631049307264-da0ec9d70304?auto=format&fit=crop&w=1000&q=80",
        "description": "A sophisticated suite with private living lounge, marble en-suite bathroom, and impressive luxury finishes.",
    },
    {
        "room_number": "FR-512",
        "category": "Family Room",
        "price": Decimal("249.00"),
        "availability": True,
        "title": "Family Comfort Hub",
        "image": "https://images.unsplash.com/photo-1595526114035-0d45ed16cfbf?auto=format&fit=crop&w=1000&q=80",
        "description": "A roomy family stay with flexible bedding layout, warm interiors, and abundant practical comfort.",
    },
    {
        "room_number": "PS-015",
        "category": "Presidential Suite",
        "price": Decimal("499.00"),
        "availability": True,
        "title": "Imperial Presidential Suite",
        "image": "https://images.unsplash.com/photo-1578683010236-d716f9a3f461?auto=format&fit=crop&w=1000&q=80",
        "description": "The hotel's signature luxury suite with grand interiors, private dining space, and ultra-exclusive penthouse appeal.",
    },
    {
        "room_number": "DR-221",
        "category": "Deluxe Room",
        "price": Decimal("179.00"),
        "availability": True,
        "title": "Deluxe Garden Escape",
        "image": "https://images.unsplash.com/photo-1591088398332-8a7791972843?auto=format&fit=crop&w=1000&q=80",
        "description": "A deluxe option with tranquil garden views, soft ambient mood lighting, and peaceful boutique vibes.",
    },
]


def build_demo_image(title, accent):
    svg = f"""
    <svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 800 520'>
        <defs>
            <linearGradient id='sky' x1='0%' y1='0%' x2='100%' y2='100%'>
                <stop offset='0%' stop-color='#eef6ff' />
                <stop offset='100%' stop-color='#dbeafe' />
            </linearGradient>
            <linearGradient id='floor' x1='0%' y1='0%' x2='100%' y2='0%'>
                <stop offset='0%' stop-color='#f6efe4' />
                <stop offset='100%' stop-color='#efe2d0' />
            </linearGradient>
        </defs>
        <rect width='800' height='520' rx='36' fill='url(#sky)' />
        <rect x='0' y='320' width='800' height='200' fill='url(#floor)' />
        <rect x='510' y='90' width='180' height='150' rx='20' fill='#f8fafc' stroke='#cbd5e1' />
        <rect x='530' y='110' width='140' height='110' rx='14' fill='{accent}' fill-opacity='0.18' />
        <rect x='88' y='258' width='324' height='96' rx='26' fill='{accent}' fill-opacity='0.12' />
        <rect x='120' y='226' width='260' height='56' rx='20' fill='{accent}' fill-opacity='0.22' />
        <rect x='88' y='280' width='304' height='92' rx='18' fill='white' stroke='#dbe4f0' />
        <rect x='98' y='288' width='138' height='76' rx='12' fill='{accent}' fill-opacity='0.18' />
        <rect x='252' y='298' width='128' height='12' rx='6' fill='#94a3b8' fill-opacity='0.35' />
        <rect x='252' y='320' width='108' height='12' rx='6' fill='#94a3b8' fill-opacity='0.22' />
        <rect x='252' y='342' width='86' height='12' rx='6' fill='#94a3b8' fill-opacity='0.18' />
        <rect x='468' y='255' width='170' height='110' rx='18' fill='white' stroke='#dbe4f0' />
        <rect x='492' y='278' width='68' height='64' rx='14' fill='{accent}' fill-opacity='0.18' />
        <rect x='574' y='278' width='40' height='64' rx='14' fill='#e2e8f0' />
        <circle cx='690' cy='310' r='24' fill='{accent}' fill-opacity='0.28' />
        <rect x='680' y='330' width='20' height='56' rx='10' fill='#cbd5e1' />
        <text x='88' y='108' fill='#0f172a' font-size='28' font-family='Poppins, Arial, sans-serif'>Aurora Haven</text>
        <text x='88' y='154' fill='#0f172a' font-size='44' font-weight='700' font-family='Poppins, Arial, sans-serif'>{title}</text>
        <text x='88' y='192' fill='#475569' font-size='22' font-family='Poppins, Arial, sans-serif'>Hotel room preview</text>
    </svg>
    """
    return f"data:image/svg+xml;charset=UTF-8,{quote(svg)}"


def seed_demo_data():
    # Only seed initial sample data if there are no categories or rooms in the database
    if Category.objects.exists() and Room.objects.exists():
        return

    category_map = {}
    for item in CATEGORY_DATA:
        category, created = Category.objects.get_or_create(name=item["name"])
        category_map[item["name"]] = category

    for item in ROOM_DATA:
        category = category_map.get(item["category"])
        if not category:
            continue
        accent = next((data["accent"] for data in CATEGORY_DATA if data["name"] == item["category"]), "#2563eb")
        img = item.get("image") or build_demo_image(item["title"], accent)
        Room.objects.get_or_create(
            room_number=item["room_number"],
            defaults={
                "category": category,
                "price": item["price"],
                "description": item["description"],
                "image": img,
                "availability": item["availability"],
            },
        )


def get_category_cards():
    cards = []
    category_meta = {item["name"]: item for item in CATEGORY_DATA}
    default_accents = ["#2563eb", "#059669", "#7c3aed", "#ea580c", "#db2777", "#0891b2", "#0f766e"]

    for idx, category in enumerate(Category.objects.all().order_by("name")):
        meta = category_meta.get(category.name, {})
        accent = meta.get("accent", default_accents[idx % len(default_accents)])
        tagline = meta.get("tagline", "Curated comfort and prime hotel experience.")
        cards.append(
            {
                "id": category.id,
                "name": category.name,
                "tagline": tagline,
                "accent": accent,
                "room_count": category.rooms.count(),
            }
        )
    return cards


def get_base_context():
    return {
        "category_cards": get_category_cards(),
        "status_choices": BOOKING_STATUS_CHOICES,
    }


def register_user(request):
    if request.user.is_authenticated:
        return redirect("home")

    form_data = {
        "first_name": "",
        "last_name": "",
        "username": "",
        "email": "",
        "phone": "",
    }

    if request.method == "POST":
        form_data = {
            "first_name": request.POST.get("first_name", "").strip(),
            "last_name": request.POST.get("last_name", "").strip(),
            "username": request.POST.get("username", "").strip(),
            "email": request.POST.get("email", "").strip(),
            "phone": request.POST.get("phone", "").strip(),
        }
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("confirm_password", "")

        if not all([*form_data.values(), password, confirm_password]):
            messages.error(request, "Please fill in all registration fields.")
        elif password != confirm_password:
            messages.error(request, "Password and confirm password do not match.")
        elif User.objects.filter(username=form_data["username"]).exists():
            messages.error(request, "This username already exists. Please choose another one.")
        elif User.objects.filter(email=form_data["email"]).exists():
            messages.error(request, "This email is already registered. Please use another email.")
        else:
            user = User.objects.create_user(
                username=form_data["username"],
                email=form_data["email"],
                password=password,
                first_name=form_data["first_name"],
                last_name=form_data["last_name"],
            )
            full_name = f"{form_data['first_name']} {form_data['last_name']}".strip() or form_data["username"]
            Guest.objects.create(user=user, name=full_name, phone=form_data["phone"])
            login(request, user)
            messages.success(request, f"Registration Successful! Welcome to Aurora Haven, {user.first_name or user.username}.")
            return redirect("home")

    context = {
        **get_base_context(),
        "form_data": form_data,
    }
    return render(request, "hotel/register.html", context)


def login_user(request):
    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            return redirect("admin_dashboard")
        return redirect("home")

    role_requested = request.GET.get("role", "") or request.POST.get("role", "")
    next_page = request.GET.get("next") or request.POST.get("next") or ""
    if role_requested == "admin" and not next_page:
        next_page = "/portal/"

    form_data = {
        "username": "",
    }

    if request.method == "POST":
        form_data["username"] = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        role_requested = request.POST.get("role", role_requested)
        user = authenticate(request, username=form_data["username"], password=password)

        if user is None:
            messages.error(request, "Incorrect username or password. Please verify your credentials and try again.")
        else:
            login(request, user)
            is_staff_user = user.is_staff or user.is_superuser
            role_text = "Staff Administrator" if is_staff_user else "Guest"
            messages.success(request, f"Login Successful! Welcome back, {user.first_name or user.username} ({role_text}).")

            if is_staff_user:
                return redirect(next_page if (next_page and next_page != "/") else "admin_dashboard")
            else:
                if next_page and "/portal/" in next_page:
                    return redirect("home")
                return redirect(next_page or "home")

    context = {
        **get_base_context(),
        "form_data": form_data,
        "next": next_page,
        "role": role_requested,
    }
    return render(request, "hotel/login.html", context)


def logout_user(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect("home")


def home(request):
    seed_demo_data()
    featured_rooms = Room.objects.select_related("category").filter(availability=True)[:6]
    context = {
        **get_base_context(),
        "featured_rooms": featured_rooms,
        "room_count": Room.objects.count(),
        "available_count": Room.objects.filter(availability=True).count(),
        "booking_count": Booking.objects.count(),
    }
    return render(request, "hotel/home.html", context)


def rooms(request):
    seed_demo_data()
    selected_category = request.GET.get("category", "")
    availability_filter = request.GET.get("availability", "")
    search_text = request.GET.get("search", "").strip()

    room_list = Room.objects.select_related("category").all().order_by("room_number")

    if selected_category:
        room_list = room_list.filter(category_id=selected_category)

    if availability_filter == "available":
        room_list = room_list.filter(availability=True)
    elif availability_filter == "unavailable":
        room_list = room_list.filter(availability=False)

    if search_text:
        room_list = room_list.filter(
            Q(room_number__icontains=search_text)
            | Q(category__name__icontains=search_text)
            | Q(description__icontains=search_text)
        )

    context = {
        **get_base_context(),
        "rooms": room_list,
        "categories": Category.objects.all().order_by("name"),
        "selected_category": selected_category,
        "availability_filter": availability_filter,
        "search_text": search_text,
    }
    return render(request, "hotel/rooms.html", context)


def room_detail(request, room_id):
    seed_demo_data()
    room = get_object_or_404(Room.objects.select_related("category"), id=room_id)
    similar_rooms = Room.objects.select_related("category").filter(category=room.category).exclude(id=room.id)[:3]
    context = {
        **get_base_context(),
        "room": room,
        "similar_rooms": similar_rooms,
    }
    return render(request, "hotel/room_detail.html", context)


@login_required(login_url="login")
def booking(request, room_id=None):
    seed_demo_data()
    selected_room = None
    if room_id:
        selected_room = get_object_or_404(Room.objects.select_related("category"), id=room_id)

    guest_profile = Guest.objects.filter(user=request.user).first()
    default_name = request.user.get_full_name() or request.user.username
    default_phone = guest_profile.phone if guest_profile else ""

    rooms_list = Room.objects.select_related("category").all().order_by("room_number")
    form_data = {
        "guest_name": default_name,
        "phone": default_phone,
        "check_in": "",
        "check_out": "",
        "room": str(room_id) if room_id else "",
    }

    if request.method == "POST":
        form_data = {
            "guest_name": request.POST.get("guest_name", "").strip(),
            "phone": request.POST.get("phone", "").strip(),
            "check_in": request.POST.get("check_in", ""),
            "check_out": request.POST.get("check_out", ""),
            "room": request.POST.get("room", ""),
        }

        if not all(form_data.values()):
            messages.error(request, "Please fill in all booking fields before continuing.")
        else:
            try:
                room = get_object_or_404(Room.objects.select_related("category"), id=form_data["room"])
                check_in = datetime.strptime(form_data["check_in"], "%Y-%m-%d").date()
                check_out = datetime.strptime(form_data["check_out"], "%Y-%m-%d").date()
            except ValueError:
                messages.error(request, "Please enter valid check-in and check-out dates.")
            else:
                if check_out <= check_in:
                    messages.error(request, "Check-out date must be after the check-in date.")
                elif not room.availability:
                    messages.error(request, "This room is currently marked as unavailable.")
                else:
                    overlap_exists = Booking.objects.filter(
                        room=room,
                        check_in__lt=check_out,
                        check_out__gt=check_in,
                    ).exclude(status="Checked-out").exists()

                    if overlap_exists:
                        messages.error(
                            request,
                            "This room is already reserved for the selected dates. Please choose another room or date.",
                        )
                    else:
                        guest, created = Guest.objects.get_or_create(
                            user=request.user,
                            defaults={
                                "name": form_data["guest_name"],
                                "phone": form_data["phone"],
                            },
                        )
                        guest.name = form_data["guest_name"]
                        guest.phone = form_data["phone"]
                        guest.save()
                        nights = (check_out - check_in).days
                        total_price = room.price * Decimal(nights)
                        booking_record = Booking.objects.create(
                            guest=guest,
                            room=room,
                            check_in=check_in,
                            check_out=check_out,
                            total_price=total_price,
                            status="Reserved",
                        )
                        return redirect("booking_confirmation", booking_id=booking_record.id)

    if form_data["room"]:
        selected_room = Room.objects.filter(id=form_data["room"]).select_related("category").first()

    context = {
        **get_base_context(),
        "rooms": rooms_list,
        "selected_room": selected_room,
        "form_data": form_data,
    }
    return render(request, "hotel/booking.html", context)


@login_required(login_url="login")
def booking_confirmation(request, booking_id):
    seed_demo_data()
    booking_record = get_object_or_404(
        Booking.objects.select_related("guest", "room", "room__category"),
        id=booking_id,
        guest__user=request.user,
    )
    context = {
        **get_base_context(),
        "booking": booking_record,
    }
    return render(request, "hotel/booking_confirmation.html", context)


@login_required(login_url="login")
def booking_history(request):
    seed_demo_data()
    bookings = Booking.objects.select_related("guest", "room", "room__category").filter(
        guest__user=request.user
    ).order_by("-created_at")
    context = {
        **get_base_context(),
        "bookings": bookings,
    }
    return render(request, "hotel/booking_history.html", context)


@login_required(login_url="login")
def update_booking_status(request, booking_id):
    booking_record = get_object_or_404(Booking, id=booking_id, guest__user=request.user)

    if request.method == "POST":
        new_status = request.POST.get("status", "")
        valid_statuses = [choice[0] for choice in BOOKING_STATUS_CHOICES]

        if new_status in valid_statuses:
            booking_record.status = new_status
            booking_record.save()
            messages.success(request, f"Booking #{booking_record.id} status updated to {new_status}.")
        else:
            messages.error(request, "Invalid booking status selected.")

    return redirect("booking_history")


@login_required(login_url="login")
def cancel_booking(request, booking_id):
    booking_record = get_object_or_404(Booking, id=booking_id, guest__user=request.user)
    if request.method == "POST":
        if booking_record.status in ["Reserved", "Checked-in"]:
            booking_record.status = "Cancelled"
            booking_record.save()
            messages.success(request, f"Booking #{booking_record.id} has been cancelled successfully.")
        else:
            messages.error(request, f"Cannot cancel a booking with status '{booking_record.status}'.")
    return redirect("booking_history")


def ai_chat_api(request):
    if request.method == "POST":
        try:
            body = json.loads(request.body.decode("utf-8")) if request.body else {}
        except Exception:
            body = {}
        message = body.get("message") or request.POST.get("message", "")
        if not message.strip():
            return JsonResponse({"error": "Message is required"}, status=400)

        response_data = ask_concierge(message, user=request.user)
        return JsonResponse(response_data)

    return JsonResponse({"error": "POST method required"}, status=405)


def ai_match_api(request):
    budget = request.GET.get("budget") or request.POST.get("budget")
    vibe = request.GET.get("vibe", "any") or request.POST.get("vibe", "any")
    guests = request.GET.get("guests", 1) or request.POST.get("guests", 1)

    matches = match_smart_rooms(budget=budget, vibe=vibe, guests=guests)
    results = []
    for m in matches:
        room = m["room"]
        results.append({
            "id": room.id,
            "room_number": room.room_number,
            "category": room.category.name,
            "price": str(room.price),
            "description": room.description,
            "image": room.image,
            "score": m["score"],
            "highlight": m["highlight"],
        })
    return JsonResponse({"matches": results})
