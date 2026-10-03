import os
import re
from decimal import Decimal
from django.db.models import Avg, Count, Sum
from .models import Booking, Category, Room


def get_gemini_or_openai_response(prompt, system_instruction):
    """
    If an API key is provided in environment variables, use it.
    Supports GEMINI_API_KEY or OPENAI_API_KEY.
    Otherwise gracefully falls back to local intelligent engine.
    """
    gemini_key = os.environ.get("GEMINI_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")

    if gemini_key:
        try:
            import urllib.request
            import json

            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
            payload = {
                "system_instruction": {"parts": [{"text": system_instruction}]},
                "contents": [{"parts": [{"text": prompt}]}],
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result["candidates"][0]["content"]["parts"][0]["text"]
        except Exception:
            pass

    if openai_key:
        try:
            import urllib.request
            import json

            url = "https://api.openai.com/v1/chat/completions"
            payload = {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.7,
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {openai_key}",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result["choices"][0]["message"]["content"]
        except Exception:
            pass

    return None


def ask_concierge(query, user=None):
    """
    Aurora AI Concierge chatbot logic.
    Combines real-time database queries with conversational intelligence.
    """
    clean_query = (query or "").lower().strip()
    available_rooms = Room.objects.filter(availability=True).select_related("category")
    categories = list(Category.objects.values_list("name", flat=True))

    suggested_rooms = []
    quick_replies = ["Show available rooms", "Rooms under ₹5000", "Check-in policy", "Book a stay"]

    # Check for budget inquiries (e.g., "under 5000", "below 3000", "cheap", "budget")
    price_match = re.search(r"(?:under|below|less than|within|\$|₹|rs\.?|inr)\s*(\d+)", clean_query)
    budget_limit = None
    if price_match:
        budget_limit = Decimal(price_match.group(1))

    # Room recommendation query
    if any(w in clean_query for w in ["recommend", "suggest", "best room", "looking for a room", "find room"]) or budget_limit:
        if budget_limit:
            matched = available_rooms.filter(price__lte=budget_limit).order_by("-price")[:3]
            if matched.exists():
                suggested_rooms = list(matched)
                reply = (
                    f"Here are top available rooms within your budget of ₹{budget_limit:.0f}/night! "
                    f"Our {matched[0].category.name} ({matched[0].room_number}) is an excellent choice."
                )
            else:
                cheapest = available_rooms.order_by("price").first()
                if cheapest:
                    suggested_rooms = [cheapest]
                    reply = (
                        f"We don't currently have rooms under ₹{budget_limit:.0f}. "
                        f"Our most affordable available option is {cheapest.category.name} ({cheapest.room_number}) at ₹{cheapest.price:.2f}/night."
                    )
                else:
                    reply = "All our rooms are currently booked. Please check back later!"
        elif any(w in clean_query for w in ["luxury", "presidential", "suite", "honeymoon", "romantic"]):
            luxury_rooms = available_rooms.filter(category__name__icontains="Suite").order_by("-price")[:2]
            if not luxury_rooms.exists():
                luxury_rooms = available_rooms.order_by("-price")[:2]
            suggested_rooms = list(luxury_rooms)
            reply = (
                "For an exquisite luxury experience, I highly recommend our premium suites with dedicated lounge areas, "
                "scenic views, and plush king bedding."
            )
        elif any(w in clean_query for w in ["family", "group", "kids", "multiple"]):
            fam_rooms = available_rooms.filter(category__name__icontains="Family")[:2]
            if not fam_rooms.exists():
                fam_rooms = available_rooms.order_by("-price")[:2]
            suggested_rooms = list(fam_rooms)
            reply = "For families and groups, our Family Rooms provide generous living space and flexible bedding."
        else:
            featured = available_rooms.order_by("price")[:3]
            suggested_rooms = list(featured)
            reply = (
                f"We have {available_rooms.count()} rooms ready for your stay! "
                "Here are our most popular choices ranging from affordable comfort to upscale luxury."
            )

    elif any(w in clean_query for w in ["check in", "check-in", "checkout", "check out", "timing", "time"]):
        reply = (
            "🕒 **Hotel Timings:**\n"
            "• **Check-in:** 2:00 PM onwards\n"
            "• **Check-out:** Up to 11:00 AM\n"
            "Early check-in and express late check-out can be requested at the reception desk."
        )

    elif any(w in clean_query for w in ["amenity", "amenities", "wifi", "pool", "food", "breakfast", "gym", "service"]):
        reply = (
            "✨ **Aurora Haven Amenities:**\n"
            "• Complimentary ultra-fast Wi-Fi\n"
            "• Rooftop Infinity Pool & Wellness Spa\n"
            "• 24/7 Fitness Center\n"
            "• Multi-cuisine Restaurant & Breakfast Buffet\n"
            "• 24/7 Room Service & Concierge Desk\n"
            "• Secure valet parking"
        )

    elif any(w in clean_query for w in ["cancel", "cancellation", "refund", "change"]):
        reply = (
            "🛡️ **Cancellation Policy:**\n"
            "You can cancel or reschedule your reservation free of charge up to 24 hours prior to check-in. "
            "Manage your bookings easily from the 'Bookings' tab in your profile."
        )

    elif any(w in clean_query for w in ["book", "reserve", "how to book"]):
        reply = (
            "To book a room:\n"
            "1. Visit the **Rooms** section to pick your preferred category.\n"
            "2. Click **'Book Now'** on any room.\n"
            "3. Select your check-in and check-out dates and confirm your stay instantly!"
        )
        first_avail = available_rooms.first()
        if first_avail:
            suggested_rooms = [first_avail]

    elif any(w in clean_query for w in ["hello", "hi", "hey", "assalam", "namaste", "good morning", "good evening"]):
        user_name = user.first_name if (user and user.is_authenticated and user.first_name) else "Guest"
        reply = (
            f"Hello {user_name}! I'm **Aurora AI**, your personal 24/7 hotel concierge. "
            f"How may I assist your stay today? You can ask me about room recommendations, pricing, amenities, or hotel policies."
        )

    elif any(w in clean_query for w in ["price", "cost", "rate", "tariff"]):
        min_price = available_rooms.aggregate(Avg("price"))
        cheapest = available_rooms.order_by("price").first()
        highest = available_rooms.order_by("-price").first()
        c_p = f"₹{cheapest.price:.0f}" if cheapest else "₹2,499"
        h_p = f"₹{highest.price:.0f}" if highest else "₹14,999"
        reply = f"Our room rates start from **{c_p}/night** up to **{h_p}/night** for the Presidential Suite. All rates include complimentary breakfast and Wi-Fi access."
        suggested_rooms = list(available_rooms[:2])

    else:
        # Try LLM if configured
        system_instruction = (
            "You are Aurora AI, the professional, courteous virtual concierge for Aurora Haven Hotel. "
            f"The hotel has categories: {', '.join(categories)}. Provide helpful, hospitable answers about hotel stays."
        )
        llm_reply = get_gemini_or_openai_response(query, system_instruction)
        if llm_reply:
            reply = llm_reply
        else:
            reply = (
                "I'm here to ensure you have a wonderful stay at Aurora Haven! "
                "Feel free to ask me to recommend a room, check prices, explain amenities, or clarify hotel timings."
            )
            suggested_rooms = list(available_rooms[:2])

    formatted_rooms = []
    for r in suggested_rooms:
        formatted_rooms.append(
            {
                "id": r.id,
                "room_number": r.room_number,
                "category": r.category.name,
                "price": str(r.price),
                "image": r.image,
            }
        )

    return {
        "reply": reply,
        "suggested_rooms": formatted_rooms,
        "quick_replies": quick_replies,
    }


def match_smart_rooms(budget=None, vibe="any", guests=1):
    """
    AI Matcher algorithm that computes affinity scores for rooms.
    """
    rooms = Room.objects.filter(availability=True).select_related("category")
    matches = []

    for room in rooms:
        score = 80
        reasons = []

        # Budget evaluation
        if budget:
            try:
                b_dec = Decimal(budget)
                if room.price <= b_dec:
                    score += 15
                    reasons.append(f"Fits easily within your ₹{b_dec:.0f} budget")
                else:
                    diff = room.price - b_dec
                    penalty = min(30, int(diff / 10))
                    score -= penalty
                    reasons.append(f"₹{diff:.0f} above stated budget")
            except Exception:
                pass

        # Vibe / Purpose evaluation
        vibe_lower = (vibe or "").lower()
        cat_lower = room.category.name.lower()
        if "luxury" in vibe_lower or "romantic" in vibe_lower:
            if "suite" in cat_lower or "presidential" in cat_lower:
                score += 15
                reasons.append("Premium luxury finishes & intimate atmosphere")
        elif "business" in vibe_lower or "work" in vibe_lower:
            if "executive" in cat_lower or "superior" in cat_lower:
                score += 15
                reasons.append("Ergonomic work setup & fast Wi-Fi")
        elif "family" in vibe_lower or int(guests) > 2:
            if "family" in cat_lower or "suite" in cat_lower:
                score += 15
                reasons.append("Spacious multi-guest layout")

        score = max(50, min(99, score))

        matches.append(
            {
                "room": room,
                "score": score,
                "highlight": reasons[0] if reasons else "High guest satisfaction rating",
            }
        )

    matches.sort(key=lambda x: x["score"], reverse=True)
    return matches[:4]


def get_admin_ai_insights():
    """
    Generates intelligent business analytics and dynamic pricing recommendations.
    """
    total_rooms = Room.objects.count()
    available_rooms = Room.objects.filter(availability=True).count()
    booked_rooms = total_rooms - available_rooms
    occupancy_rate = round((booked_rooms / total_rooms * 100), 1) if total_rooms else 0

    total_revenue = Booking.objects.exclude(status="Cancelled").aggregate(Sum("total_price"))["total_price__sum"] or Decimal("0.00")
    total_bookings = Booking.objects.count()
    active_bookings = Booking.objects.filter(status__in=["Reserved", "Checked-in"]).count()

    # Dynamic Pricing Recommendation
    if occupancy_rate >= 80:
        pricing_status = "High Demand Surge"
        pricing_badge = "success"
        pricing_action = "+15% Rate Adjustment"
        pricing_advice = (
            "Occupancy is exceptionally high (>80%). AI recommends increasing rates for remaining rooms by 10-15% "
            "to maximize RevPAR (Revenue Per Available Room)."
        )
    elif occupancy_rate <= 35:
        pricing_status = "Low Occupancy Alert"
        pricing_badge = "warning"
        pricing_action = "Promotional Discount -10%"
        pricing_advice = (
            "Occupancy is below 35%. AI recommends launching a 10% 'Early Bird' or weekend package promotion "
            "to stimulate booking velocity."
        )
    else:
        pricing_status = "Optimal Demand"
        pricing_badge = "info"
        pricing_action = "Maintain Standard Rates"
        pricing_advice = (
            "Occupancy is healthy and balanced. Current rate tiers are performing within the optimal target window."
        )

    # Forecast / Predictions
    popular_category = (
        Booking.objects.values("room__category__name")
        .annotate(count=Count("id"))
        .order_by("-count")
        .first()
    )
    popular_name = popular_category["room__category__name"] if popular_category else "Standard Room"

    return {
        "occupancy_rate": occupancy_rate,
        "total_revenue": total_revenue,
        "total_bookings": total_bookings,
        "active_bookings": active_bookings,
        "booked_rooms": booked_rooms,
        "available_rooms": available_rooms,
        "pricing_status": pricing_status,
        "pricing_badge": pricing_badge,
        "pricing_action": pricing_action,
        "pricing_advice": pricing_advice,
        "popular_category": popular_name,
    }
