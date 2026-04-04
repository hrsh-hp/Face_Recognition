"""
Helper utilities for SecureFace — Biometric Access Control System.
"""

from django.core.mail import send_mail
from django.conf import settings as django_settings
import logging

security_logger = logging.getLogger('security')


def send_email_token(email, email_token):
    """Send email verification link to user."""
    try:
        domain = getattr(django_settings, 'SITE_DOMAIN', 'http://127.0.0.1:8000')
        subject = "SecureFace — Verify Your Email"
        verification_url = f"{domain}/verify/{email_token}"

        message = (
            f"Welcome to SecureFace Biometric Access Control System!\n\n"
            f"Click the link below to verify your email address:\n"
            f"{verification_url}\n\n"
            f"If you did not create this account, please ignore this email.\n\n"
            f"— SecureFace Security Team"
        )

        email_from = django_settings.EMAIL_HOST_USER
        send_mail(subject, message, email_from, [email])
        security_logger.info(f"Verification email sent to {email}")
        return True

    except Exception as e:
        security_logger.error(f"Failed to send verification email to {email}: {e}")
        return False


def get_client_ip(request):
    """Extract client IP from request, handling proxies."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '0.0.0.0')