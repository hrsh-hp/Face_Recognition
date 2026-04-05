"""
Views for SecureFace — Biometric Access Control System.

Security-hardened views with audit logging, rate limiting,
confidence scoring, and proper CSRF handling.
"""

from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib import messages
from django.core.cache import cache
from django.utils import timezone
from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from django.conf import settings

import uuid
import json
import logging
import face_recognition
import base64
import cv2
import numpy as np
from PIL import Image
from io import BytesIO
from datetime import timedelta

from .models import AccessLog, LoginAttempt, SecurityAlert
from .helpers import send_email_token, get_client_ip

User = get_user_model()
security_logger = logging.getLogger('security')

known_faces = {}


# ─── FACE ENCODING UTILITIES ────────────────────────────────────────────────────

def get_known_face_encoding():
    """Load all registered face encodings from the database."""
    known_face_encodings = {}
    for face_obj in User.objects.filter(is_superuser=False, user_image__isnull=False):
        try:
            if not face_obj.user_image or ',' not in face_obj.user_image:
                continue
            known_image_data = base64.b64decode(face_obj.user_image.split(',')[1])
            known_image = Image.open(BytesIO(known_image_data))
            encodings = face_recognition.face_encodings(np.array(known_image))
            if encodings:
                known_face_encodings[face_obj.email] = encodings[0]
        except Exception as e:
            security_logger.error(f"Failed to encode face for {face_obj.email}: {e}")
    return known_face_encodings


def update_known_faces():
    """Refresh the cached face encodings."""
    faces = get_known_face_encoding()
    cache.set('known_faces', faces, timeout=None)
    return faces


# ─── INDEX / HOME ────────────────────────────────────────────────────────────────

@login_required(login_url='/login/')
def index(request):
    """Main face recognition page — requires authentication."""
    known = cache.get('known_faces')
    if known is None:
        update_known_faces()

    # Get recent access logs for the activity feed
    recent_logs = AccessLog.objects.all()[:20]
    total_users = User.objects.filter(is_superuser=False).count()
    today = timezone.now().date()
    today_scans = AccessLog.objects.filter(timestamp__date=today).count()
    today_granted = AccessLog.objects.filter(timestamp__date=today, result='granted').count()
    today_denied = AccessLog.objects.filter(timestamp__date=today, result__in=['denied', 'unknown']).count()

    context = {
        'recent_logs': recent_logs,
        'total_users': total_users,
        'today_scans': today_scans,
        'today_granted': today_granted,
        'today_denied': today_denied,
    }
    return render(request, 'index.html', context)


# ─── FACE RECOGNITION ───────────────────────────────────────────────────────────

@login_required(login_url='/login/')
def recognize_face(request):
    """
    Face recognition endpoint.
    Accepts POST with base64 image, returns recognition result with confidence.
    Logs every attempt to AccessLog.
    """
    if request.method != "POST":
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    known = cache.get('known_faces', {})
    if not known:
        known = update_known_faces()

    ip = get_client_ip(request)
    tolerance = getattr(settings, 'FACE_RECOGNITION_TOLERANCE', 0.5)

    try:
        image_data = request.POST.get('imageData', '')
        if not image_data or ',' not in image_data:
            return JsonResponse({'error': 'Invalid image data', 'success': False})

        # Decode base64 image
        img_data = base64.b64decode(image_data.split(',')[1])
        image = Image.open(BytesIO(img_data))
        frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

        # Detect faces
        face_locations = face_recognition.face_locations(frame, number_of_times_to_upsample=1)
        face_encodings = face_recognition.face_encodings(frame, face_locations)

        if not face_encodings:
            AccessLog.objects.create(
                ip_address=ip, result='denied',
                confidence_score=0, recognized_email='No face detected'
            )
            return JsonResponse({
                'student': {'email': 'No Face Detected', 'status': 'no_face'},
                'success': True,
                'confidence': 0,
                'faces_found': 0
            })

        # Compare against known faces
        best_match = None
        best_confidence = 0
        student = {'email': 'Unknown', 'status': 'unknown'}

        for face_encoding in face_encodings:
            if not known:
                break

            face_distances = face_recognition.face_distance(
                list(known.values()), face_encoding
            )
            matches = face_recognition.compare_faces(
                list(known.values()), face_encoding, tolerance=tolerance
            )

            if True in matches:
                best_match_idx = np.argmin(face_distances)
                confidence = round((1 - face_distances[best_match_idx]) * 100, 1)

                if confidence > best_confidence:
                    best_confidence = confidence
                    email = list(known.keys())[best_match_idx]
                    best_match = email

        # Build response
        _, jpeg = cv2.imencode('.jpeg', frame)
        response_img = base64.b64encode(jpeg.tobytes()).decode('utf-8')

        if best_match and best_confidence >= (getattr(settings, 'FACE_CONFIDENCE_THRESHOLD', 0.55) * 100):
            recognized_user = User.objects.filter(email=best_match).first()
            if recognized_user:
                student = {
                    'email': best_match,
                    'name': recognized_user.name(),
                    'enrollment': recognized_user.enrollment,
                    'department': recognized_user.department,
                    'status': 'granted',
                }

                AccessLog.objects.create(
                    user=recognized_user,
                    ip_address=ip,
                    result='granted',
                    confidence_score=best_confidence,
                    recognized_email=best_match,
                )
                security_logger.info(f"ACCESS GRANTED: {best_match} (confidence: {best_confidence}%) from {ip}")
        else:
            result_type = 'unknown'
            AccessLog.objects.create(
                ip_address=ip,
                result='unknown',
                confidence_score=best_confidence,
                recognized_email='Unknown',
            )
            security_logger.warning(f"UNKNOWN FACE detected from {ip} (best confidence: {best_confidence}%)")

            # Create security alert for unknown faces
            unknown_count_today = AccessLog.objects.filter(
                result='unknown',
                timestamp__date=timezone.now().date(),
                ip_address=ip
            ).count()

            if unknown_count_today >= 3:
                SecurityAlert.objects.get_or_create(
                    alert_type='unknown_face',
                    ip_address=ip,
                    resolved=False,
                    defaults={
                        'severity': 'medium',
                        'description': f'Multiple unknown face detections ({unknown_count_today}) from IP {ip}',
                    }
                )

        return JsonResponse({
            'student': student,
            'image': response_img,
            'success': True,
            'confidence': best_confidence,
            'faces_found': len(face_encodings),
        })

    except Exception as e:
        security_logger.error(f"Face recognition error from {ip}: {str(e)}")
        AccessLog.objects.create(
            ip_address=ip, result='error',
            confidence_score=0, recognized_email=f'Error: {str(e)[:100]}'
        )
        return JsonResponse({'error': str(e), 'success': False})


# ─── REGISTRATION ────────────────────────────────────────────────────────────────

def register(request):
    """User registration with face biometric enrollment."""
    if request.user.is_authenticated:
        return redirect('Auth:index')

    if request.method == "POST":
        ip = get_client_ip(request)
        try:
            email = request.POST.get('email', '').strip()
            phone_num = request.POST.get('phone_num', '').strip()
            password = request.POST.get('password', '')  # Fixed typo: was 'pasword'
            enrollment = request.POST.get('enrollment', '').strip()
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            user_image = request.POST.get('image_base64', '')
            department = request.POST.get('department', 'general').strip()

            # Validation
            if not email or not password:
                messages.error(request, "Email and password are required.")
                return redirect('Auth:register')

            if len(password) < 8:
                messages.error(request, "Password must be at least 8 characters.")
                return redirect('Auth:register')

            if User.objects.filter(email=email).exists():
                messages.error(request, "An account with this email already exists.")
                return redirect('Auth:register')

            if not user_image:
                messages.error(request, "Face biometric image is required for enrollment.")
                return redirect('Auth:register')

            if not first_name:
                first_name = email.split('@')[0]

            email_token = str(uuid.uuid4())
            user = User.objects.create(
                email=email,
                phone_num=phone_num if phone_num else None,
                first_name=first_name,
                last_name=last_name,
                user_image=user_image,
                enrollment=int(enrollment) if enrollment else None,
                department=department,
            )
            user.set_password(password)
            user.email_token = email_token
            user.save()

            security_logger.info(f"NEW REGISTRATION: {email} from {ip}")

            email_sent = send_email_token(email, email_token)
            if email_sent:
                messages.success(request, "Registration successful! A verification email has been sent.")
            else:
                messages.warning(request, "Registered, but couldn't send verification email. Contact admin.")

            return redirect('Auth:login_page')

        except Exception as e:
            security_logger.error(f"Registration error from {ip}: {str(e)}")
            messages.error(request, "Registration failed. Please try again.")
            return redirect('Auth:register')

    return render(request, 'register.html')


# ─── EMAIL VERIFICATION ─────────────────────────────────────────────────────────

def verify(request, email_token):
    """Verify user email via token link."""
    try:
        user_obj = User.objects.filter(email_token=email_token).first()

        if not user_obj:
            messages.error(request, "Invalid verification link.")
            return redirect('Auth:register')

        if user_obj.is_email_verified:
            messages.info(request, "Your email is already verified. You can log in.")
            return redirect('Auth:login_page')

        user_obj.is_email_verified = True
        user_obj.save()
        security_logger.info(f"EMAIL VERIFIED: {user_obj.email}")
        messages.success(request, "Email verified successfully! You can now log in.")
        return redirect('Auth:login_page')

    except Exception as e:
        security_logger.error(f"Verification error: {str(e)}")
        messages.error(request, "Verification failed.")
        return redirect('Auth:register')


# ─── LOGIN ───────────────────────────────────────────────────────────────────────

def login_page(request):
    """Login with email + password, with brute force protection."""
    if request.user.is_authenticated:
        return redirect('Auth:index')

    if request.method == "POST":
        ip = get_client_ip(request)
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        user_agent = request.META.get('HTTP_USER_AGENT', '')

        try:
            user_obj = User.objects.filter(email=email).first()

            if user_obj is None:
                LoginAttempt.objects.create(
                    email=email, ip_address=ip,
                    success=False, user_agent=user_agent
                )
                security_logger.warning(f"LOGIN FAILED: Unknown email {email} from {ip}")
                messages.error(request, "Invalid email or password.")
                return redirect('Auth:login_page')

            # Check account lockout
            if user_obj.is_locked:
                if user_obj.last_failed_login:
                    lockout_end = user_obj.last_failed_login + timedelta(minutes=15)
                    if timezone.now() < lockout_end:
                        remaining = (lockout_end - timezone.now()).seconds // 60
                        messages.error(
                            request,
                            f"Account locked due to too many failed attempts. Try again in {remaining + 1} minutes."
                        )
                        return redirect('Auth:login_page')
                    else:
                        # Unlock after cooldown
                        user_obj.is_locked = False
                        user_obj.failed_login_count = 0
                        user_obj.save()

            if not user_obj.is_email_verified:
                messages.warning(request, "Please verify your email before logging in.")
                return redirect('Auth:login_page')

            user = authenticate(email=email, password=password)
            if user is None:
                # Track failed attempts
                user_obj.failed_login_count += 1
                user_obj.last_failed_login = timezone.now()

                max_attempts = getattr(settings, 'MAX_LOGIN_ATTEMPTS', 5)
                if user_obj.failed_login_count >= max_attempts:
                    user_obj.is_locked = True
                    SecurityAlert.objects.create(
                        alert_type='brute_force',
                        severity='high',
                        description=f'Account {email} locked after {max_attempts} failed login attempts from IP {ip}',
                        ip_address=ip,
                    )
                    security_logger.critical(f"ACCOUNT LOCKED: {email} after {max_attempts} failed attempts from {ip}")

                user_obj.save()

                LoginAttempt.objects.create(
                    email=email, ip_address=ip,
                    success=False, user_agent=user_agent
                )
                remaining = max_attempts - user_obj.failed_login_count
                if remaining > 0:
                    messages.error(request, f"Invalid password. {remaining} attempts remaining.")
                else:
                    messages.error(request, "Account locked. Too many failed attempts.")
                return redirect('Auth:login_page')

            # Successful login — reset counters
            user_obj.failed_login_count = 0
            user_obj.is_locked = False
            user_obj.save()

            LoginAttempt.objects.create(
                email=email, ip_address=ip,
                success=True, user_agent=user_agent
            )

            login(request, user)
            security_logger.info(f"LOGIN SUCCESS: {email} from {ip}")
            return redirect('Auth:index')

        except Exception as e:
            security_logger.error(f"Login error: {str(e)}")
            messages.error(request, "An error occurred. Please try again.")
            return redirect('Auth:login_page')

    return render(request, 'login_page.html')


# ─── LOGOUT ──────────────────────────────────────────────────────────────────────

@login_required(login_url='/login/')
def logout_view(request):
    """Secure logout — clears session."""
    email = request.user.email
    ip = get_client_ip(request)
    security_logger.info(f"LOGOUT: {email} from {ip}")
    logout(request)
    messages.success(request, "You have been securely logged out.")
    return redirect('Auth:login_page')


# ─── SECURITY DASHBOARD ─────────────────────────────────────────────────────────

@login_required(login_url='/login/')
def dashboard(request):
    """Security monitoring dashboard for admin/superuser."""
    if not request.user.is_staff:
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('Auth:index')

    today = timezone.now().date()
    last_7_days = today - timedelta(days=7)

    # Stats
    total_users = User.objects.filter(is_superuser=False).count()
    total_scans = AccessLog.objects.count()
    today_scans = AccessLog.objects.filter(timestamp__date=today).count()
    today_granted = AccessLog.objects.filter(timestamp__date=today, result='granted').count()
    today_denied = AccessLog.objects.filter(timestamp__date=today, result__in=['denied', 'unknown']).count()
    active_alerts = SecurityAlert.objects.filter(resolved=False).count()

    # Recent logs
    recent_logs = AccessLog.objects.all()[:50]
    recent_alerts = SecurityAlert.objects.filter(resolved=False)[:10]
    recent_logins = LoginAttempt.objects.all()[:30]

    # 7-day chart data
    daily_stats = (
        AccessLog.objects
        .filter(timestamp__date__gte=last_7_days)
        .annotate(date=TruncDate('timestamp'))
        .values('date')
        .annotate(
            granted=Count('id', filter=Q(result='granted')),
            denied=Count('id', filter=Q(result__in=['denied', 'unknown'])),
            total=Count('id'),
        )
        .order_by('date')
    )

    chart_labels = []
    chart_granted = []
    chart_denied = []
    for stat in daily_stats:
        chart_labels.append(stat['date'].strftime('%b %d'))
        chart_granted.append(stat['granted'])
        chart_denied.append(stat['denied'])

    context = {
        'total_users': total_users,
        'total_scans': total_scans,
        'today_scans': today_scans,
        'today_granted': today_granted,
        'today_denied': today_denied,
        'active_alerts': active_alerts,
        'recent_logs': recent_logs,
        'recent_alerts': recent_alerts,
        'recent_logins': recent_logins,
        'chart_labels': json.dumps(chart_labels),
        'chart_granted': json.dumps(chart_granted),
        'chart_denied': json.dumps(chart_denied),
    }
    return render(request, 'dashboard.html', context)


# ─── API ENDPOINTS ───────────────────────────────────────────────────────────────

@login_required(login_url='/login/')
def api_access_logs(request):
    """JSON API for access logs (used by dashboard DataTable)."""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Forbidden'}, status=403)

    logs = AccessLog.objects.all()[:200].values(
        'id', 'timestamp', 'ip_address', 'result',
        'confidence_score', 'recognized_email'
    )
    return JsonResponse({'data': list(logs)}, safe=False)


@login_required(login_url='/login/')
def api_stats(request):
    """JSON API for dashboard stats."""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Forbidden'}, status=403)

    today = timezone.now().date()
    stats = {
        'total_users': User.objects.filter(is_superuser=False).count(),
        'today_scans': AccessLog.objects.filter(timestamp__date=today).count(),
        'today_granted': AccessLog.objects.filter(timestamp__date=today, result='granted').count(),
        'today_denied': AccessLog.objects.filter(timestamp__date=today, result__in=['denied', 'unknown']).count(),
        'active_alerts': SecurityAlert.objects.filter(resolved=False).count(),
    }
    return JsonResponse(stats)


@login_required(login_url='/login/')
def resolve_alert(request, alert_id):
    """Resolve a security alert."""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Forbidden'}, status=403)

    try:
        alert = SecurityAlert.objects.get(id=alert_id)
        alert.resolved = True
        alert.resolved_at = timezone.now()
        alert.save()
        return JsonResponse({'success': True})
    except SecurityAlert.DoesNotExist:
        return JsonResponse({'error': 'Alert not found'}, status=404)