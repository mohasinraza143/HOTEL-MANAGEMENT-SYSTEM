# Aurora Haven - AI-Powered Hotel Management System 🏨✨

A full-featured, luxury Hotel Management System built with **Python & Django**, enhanced with **24/7 AI Concierge Intelligence**, a dedicated **Staff Admin Portal**, and ready for **1-click deployment on Render**.

---

## 🌟 Key Features

### 1. 🤖 AI Intelligence Suite
- **Aurora AI 24/7 Concierge**: Floating interactive virtual assistant on all guest pages. Answers queries regarding room pricing, amenities, check-in policies, and provides direct room booking assistance.
- **Smart AI Room Matcher**: Guests specify their budget and trip style (Luxury, Business, Family, Budget) to get instant AI Affinity Scores and recommended rooms.
- **Admin AI Insights**: Staff dashboard features live occupancy analysis, demand surge forecasting, and dynamic pricing suggestions to maximize RevPAR.
- **Extensible AI Core**: Built-in intelligent NLP rules ensure 100% functionality out-of-the-box, with seamless auto-switching to Gemini or OpenAI LLMs when `GEMINI_API_KEY` or `OPENAI_API_KEY` is configured.

### 2. 🛡️ Dedicated Staff Admin Portal
Accessible at `/portal/` for staff & admin members:
- **Executive Dashboard**: Live revenue, active bookings, occupancy rate, and recent reservations.
- **Room Inventory Control**: Add new rooms, edit details, upload room images, toggle instant availability.
- **Reservation Manager**: Search, filter, and update booking status (`Reserved` &rarr; `Checked-in` &rarr; `Checked-out` / `Cancelled`) with one click.
- **Category Manager**: Add and manage room categories.
- **Guest Directory**: View customer profiles, contact numbers, and lifetime spend.

### 3. 🛌 Guest Experience
- **Luxury Room Catalog**: Compare categories, real-time availability, and transparent pricing.
- **Seamless Booking Flow**: Real-time date conflict validation and instant booking confirmation.
- **Self-Service Guest Dashboard**: View reservation history with 1-click booking cancellation for reserved stays.

---

## 🔑 Default Admin Credentials

- **URL**: `http://127.0.0.1:8000/portal/` or `http://127.0.0.1:8000/admin/`
- **Username**: `admin`
- **Password**: `admin123`
- **Email**: `admin@aurorahaven.com`

---

## 🚀 Running Locally

1. Open your terminal in `hotelmanagement/hotelmanagement`:
   ```bash
   cd hotelmanagement
   ```
2. Run database migrations:
   ```bash
   python manage.py migrate
   ```
3. Run the development server:
   ```bash
   python manage.py runserver
   ```
4. Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.

---

## ☁️ Deploying to Render

This repository includes `render.yaml`, `build.sh`, and `requirements.txt` pre-configured for Render.

### Method 1: Using Render Blueprint (Recommended)
1. Push your repository to GitHub.
2. Log into [Render.com](https://render.com).
3. Click **New +** &rarr; **Blueprint**.
4. Connect this GitHub repository.
5. Render will detect `render.yaml` and set up the web service automatically!

### Method 2: Manual Web Service
1. In Render, click **New +** &rarr; **Web Service**.
2. Connect your GitHub repository.
3. Set the following settings:
   - **Environment**: `Python 3`
   - **Root Directory**: `hotelmanagement` (or leave empty if using root `build.sh`)
   - **Build Command**: `./build.sh`
   - **Start Command**: `gunicorn hotelmanagement.wsgi:application`
4. Add Environment Variables:
   - `DEBUG`: `False`
   - `ALLOWED_HOSTS`: `*`
   - `SECRET_KEY`: *(Generate a secure random string)*
   - `DJANGO_SUPERUSER_USERNAME`: `admin`
   - `DJANGO_SUPERUSER_PASSWORD`: `admin123`
