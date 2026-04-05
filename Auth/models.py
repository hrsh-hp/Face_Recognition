from django.db import models
from django.contrib.auth.models import AbstractUser
from .managers import UserManager


class KnownFace(models.Model):
    name = models.CharField(max_length=250)
    image = models.TextField(default='none')
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Known Face"
        verbose_name_plural = "Known Faces"


class CustomUser(AbstractUser):
    username = None
    last_name = models.CharField(max_length=150, blank=True, null=True)
    phone_num = models.CharField(max_length=12, unique=True, null=True, blank=True)
    email = models.EmailField(unique=True, max_length=254)
    email_token = models.CharField(max_length=100, null=True, blank=True)
    is_email_verified = models.BooleanField(default=False)
    forgot_pass_token = models.CharField(max_length=100, null=True, blank=True)
    user_image = models.TextField(blank=True, null=True)
    register_date = models.DateTimeField(auto_now_add=True)
    enrollment = models.IntegerField(unique=True, null=True, blank=True)
    department = models.CharField(max_length=100, default="general")
    is_locked = models.BooleanField(default=False)  # Account lockout
    failed_login_count = models.IntegerField(default=0)
    last_failed_login = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def name(self):
        first = self.first_name or ''
        last = self.last_name or ''
        return f"{first} {last}".strip() or self.email

    def __str__(self):
        return self.email

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"


class AccessLog(models.Model):
    """Records every face recognition attempt — core security feature."""
    RESULT_CHOICES = [
        ('granted', 'Access Granted'),
        ('denied', 'Access Denied'),
        ('unknown', 'Unknown Face'),
        ('error', 'Error'),
    ]

    user = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='access_logs'
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    result = models.CharField(max_length=10, choices=RESULT_CHOICES)
    confidence_score = models.FloatField(null=True, blank=True)
    recognized_email = models.CharField(max_length=254, blank=True, default='')
    snapshot = models.TextField(blank=True, null=True)  # Base64 snapshot

    def __str__(self):
        return f"[{self.result.upper()}] {self.recognized_email or 'Unknown'} @ {self.timestamp}"

    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Access Log"
        verbose_name_plural = "Access Logs"


class LoginAttempt(models.Model):
    """Records every login attempt for security auditing."""
    email = models.CharField(max_length=254)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    success = models.BooleanField(default=False)
    user_agent = models.TextField(blank=True, default='')

    def __str__(self):
        status = "✓" if self.success else "✗"
        return f"[{status}] {self.email} @ {self.timestamp}"

    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Login Attempt"
        verbose_name_plural = "Login Attempts"


class SecurityAlert(models.Model):
    """Flags suspicious activity for the security dashboard."""
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    ALERT_TYPES = [
        ('unknown_face', 'Unknown Face Detected'),
        ('brute_force', 'Brute Force Attempt'),
        ('account_locked', 'Account Locked'),
        ('multiple_failures', 'Multiple Failed Recognitions'),
        ('suspicious_ip', 'Suspicious IP Activity'),
    ]

    alert_type = models.CharField(max_length=30, choices=ALERT_TYPES)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='medium')
    description = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"[{self.severity.upper()}] {self.get_alert_type_display()} @ {self.timestamp}"

    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Security Alert"
        verbose_name_plural = "Security Alerts"


# Signal to update face cache when users change
from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver


@receiver(pre_save, sender=CustomUser)
def track_image_change(sender, instance, **kwargs):
    """Track whether user_image changed so we only re-encode when needed."""
    if instance.pk:
        try:
            old = CustomUser.objects.get(pk=instance.pk)
            instance._image_changed = (old.user_image != instance.user_image)
        except CustomUser.DoesNotExist:
            instance._image_changed = True
    else:
        # New user
        instance._image_changed = bool(instance.user_image)


@receiver(post_save, sender=CustomUser)
def update_known_faces_on_image_change(sender, instance, created, **kwargs):
    """Only re-encode faces when user_image actually changed or a new user is created with an image."""
    image_changed = getattr(instance, '_image_changed', False)
    if image_changed or (created and instance.user_image):
        from .views import update_known_faces
        update_known_faces()


@receiver(post_delete, sender=CustomUser)
def update_known_faces_on_delete(sender, instance, **kwargs):
    from .views import update_known_faces
    update_known_faces()