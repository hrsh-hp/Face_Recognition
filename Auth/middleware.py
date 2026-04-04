"""
Security Middleware for SecureFace — Biometric Access Control System.

Provides:
- Security response headers
- Request/IP logging
- Rate limiting for sensitive endpoints
"""

import time
import logging
from django.http import JsonResponse
from django.core.cache import cache

security_logger = logging.getLogger('security')


class SecurityHeadersMiddleware:
    """Adds security headers to every response."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'camera=(self), microphone=()'
        return response


class RequestLoggingMiddleware:
    """Logs all requests with IP + path for security auditing."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ip = self.get_client_ip(request)
        path = request.path
        method = request.method
        user = request.user if hasattr(request, 'user') and request.user.is_authenticated else 'Anonymous'

        response = self.get_response(request)

        # Log non-static requests
        if not path.startswith('/static/') and not path.startswith('/admin/jsi18n'):
            security_logger.info(
                f"{method} {path} | IP: {ip} | User: {user} | Status: {response.status_code}"
            )

        return response

    @staticmethod
    def get_client_ip(request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '0.0.0.0')


class RateLimitMiddleware:
    """
    Rate limiting for sensitive endpoints.
    Blocks IPs that exceed max requests within the time window.
    """

    RATE_LIMITED_PATHS = {
        '/login/': {'max_requests': 10, 'window': 900},       # 10 per 15 min
        '/face_recognize/': {'max_requests': 60, 'window': 300},  # 60 per 5 min
        '/register/': {'max_requests': 5, 'window': 900},     # 5 per 15 min
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method == 'POST':
            path = request.path
            if path in self.RATE_LIMITED_PATHS:
                ip = RequestLoggingMiddleware.get_client_ip(request)
                limits = self.RATE_LIMITED_PATHS[path]
                cache_key = f"ratelimit:{ip}:{path}"

                request_count = cache.get(cache_key, 0)

                if request_count >= limits['max_requests']:
                    security_logger.warning(
                        f"RATE LIMITED: {ip} exceeded {limits['max_requests']} "
                        f"requests to {path}"
                    )
                    return JsonResponse({
                        'error': 'Too many requests. Please try again later.',
                        'retry_after': limits['window']
                    }, status=429)

                cache.set(cache_key, request_count + 1, limits['window'])

        return self.get_response(request)
