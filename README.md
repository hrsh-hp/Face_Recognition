# 🛡️ SecureFace — Biometric Access Control & Surveillance System

A **cybersecurity-focused** biometric access control system built with Django and real-time face recognition. Designed as a college project demonstrating security best practices including audit logging, brute force protection, rate limiting, and a modern dark-themed security dashboard.

---

## 📌 Features

### 🔐 Security
- **Face Recognition Authentication** — Real-time webcam-based biometric identification using `face_recognition` library
- **Confidence Scoring** — Face match percentage displayed with configurable threshold (default: 55%)
- **Brute Force Protection** — Account auto-locks after 5 failed login attempts with 15-minute cooldown
- **Rate Limiting** — Custom middleware limiting login (10/15min), scan (60/5min), and registration (5/15min) attempts
- **CSRF Protection** — Full CSRF token enforcement on all forms and AJAX requests
- **Security Headers** — X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, Referrer-Policy, Permissions-Policy
- **Session Management** — 30-minute timeout, expires on browser close, HTTP-only cookies
- **Audit Logging** — Every request logged to `security.log`, every login/scan recorded in database
- **Security Alerts** — Auto-generated alerts for unknown faces, brute force attempts, and account lockouts
- **Email Verification** — Token-based email verification before account activation

### 🎨 User Interface
- **Dark Cybersecurity Theme** — Navy/charcoal background with neon green accents and glassmorphism
- **Control Center** — Live webcam with scan-line overlay, ACCESS GRANTED/DENIED animated banners
- **3-Step Registration Wizard** — Personal Info → Password (with strength meter) → Biometric Enrollment (webcam capture)
- **Security Dashboard** — Chart.js analytics, access log tables, alert management (admin only)
- **Toast Notifications** — Animated notification system replacing basic alerts
- **Responsive Design** — Works on desktop and mobile

### 📊 Monitoring & Analytics
- **Access Log** — Every face recognition attempt recorded (user, IP, confidence, result, timestamp)
- **Login Attempts** — Track all login events with IP, user agent, success/failure
- **7-Day Trend Charts** — Visual analytics of access granted vs denied over time
- **Security Alerts Dashboard** — View and resolve alerts for suspicious activity

---

## 🏗️ Tech Stack

| Component | Technology |
|-----------|-----------|
| **Backend** | Django 5.0.1 (Python) |
| **Face Recognition** | `face_recognition`, `dlib`, OpenCV |
| **Database** | SQLite |
| **Frontend** | Vanilla HTML/CSS/JS, Chart.js |
| **Authentication** | Django Auth + Email Verification |
| **Security** | Custom Middleware (Rate Limiting, Headers, Logging) |

---

## 📁 Project Structure

```
Face_Recognition/
├── Auth/                        # Main application
│   ├── middleware.py             # Security middleware (rate limiting, headers, logging)
│   ├── models.py                # User, AccessLog, LoginAttempt, SecurityAlert
│   ├── views.py                 # All views with audit logging
│   ├── helpers.py               # Email & utility functions
│   ├── admin.py                 # Rich admin configuration
│   ├── urls.py                  # URL routing
│   ├── managers.py              # Custom user manager
│   ├── static/css/theme.css     # Cybersecurity dark theme (700+ lines)
│   └── templates/
│       ├── base.html            # Base layout with navbar & toasts
│       ├── login_page.html      # Login with glassmorphic card
│       ├── register.html        # 3-step enrollment wizard
│       ├── index.html           # Control center (webcam + stats)
│       └── dashboard.html       # Admin security dashboard
├── Face_Recognition/            # Django project settings
│   ├── settings.py              # Security-hardened configuration
│   ├── urls.py                  # Root URL config
│   └── wsgi.py
├── manage.py
├── requirements.txt
├── .env.example                 # Environment variable template
└── security.log                 # Auto-generated security audit log
```

---

## 🚀 Setup & Installation

### Prerequisites
- Python 3.9+
- pip
- (Linux) `cmake` and `build-essential` for dlib compilation

### 1. Clone the repository
```bash
git clone https://github.com/hrsh06/Face_Recognition.git
cd Face_Recognition
```

### 2. Create and activate virtual environment
```bash
python -m venv venv
source venv/bin/activate        # Linux/Mac
# or
.\venv\Scripts\activate         # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
```bash
cp .env.example .env
```
Edit `.env` and fill in your values:
```
SECRET_KEY=your-django-secret-key
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
SITE_DOMAIN=http://127.0.0.1:8000
```

> **Generate a SECRET_KEY:**
> ```python
> python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
> ```

### 5. Run migrations
```bash
python manage.py makemigrations Auth
python manage.py migrate
```

### 6. Create admin user
```bash
python manage.py createsuperuser
```

### 7. Start the server
```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000/login/` to access the system.

---

## 🔑 Usage

| Page | URL | Access |
|------|-----|--------|
| Login | `/login/` | Public |
| Register | `/register/` | Public |
| Control Center | `/` | Authenticated users |
| Security Dashboard | `/dashboard/` | Admin/Staff only |
| Admin Panel | `/admin/` | Superuser only |

### User Flow
1. **Register** → Fill personal info → Set password → Capture face biometric
2. **Verify Email** → Click link sent to your email
3. **Login** → Email + password authentication
4. **Control Center** → Click "Scan & Identify" to test face recognition
5. **Dashboard** (admin) → Monitor access logs, alerts, and trends

---

## 🛡️ Security Architecture

```
Request → SecurityHeadersMiddleware → RequestLoggingMiddleware → RateLimitMiddleware → View
                    ↓                         ↓                        ↓
             Add XSS/CSRF/          Log to security.log         Check request
             Frame headers                                     count per IP
```

### Models
- **AccessLog** — Records every face scan (user, IP, result, confidence, timestamp)
- **LoginAttempt** — Records every login (email, IP, success, user agent, timestamp)
- **SecurityAlert** — Auto-generated flags (unknown faces, brute force, lockouts)