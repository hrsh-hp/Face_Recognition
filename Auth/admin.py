from django.contrib import admin
from .models import CustomUser, KnownFace, AccessLog, LoginAttempt, SecurityAlert


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'department', 'is_email_verified', 'is_locked', 'register_date')
    list_filter = ('is_email_verified', 'is_locked', 'department', 'is_staff')
    search_fields = ('email', 'first_name', 'last_name', 'enrollment')
    readonly_fields = ('register_date', 'last_failed_login')


@admin.register(KnownFace)
class KnownFaceAdmin(admin.ModelAdmin):
    list_display = ('name', 'timestamp')
    search_fields = ('name',)


@admin.register(AccessLog)
class AccessLogAdmin(admin.ModelAdmin):
    list_display = ('recognized_email', 'result', 'confidence_score', 'ip_address', 'timestamp')
    list_filter = ('result', 'timestamp')
    search_fields = ('recognized_email', 'ip_address')
    date_hierarchy = 'timestamp'
    readonly_fields = ('timestamp',)


@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    list_display = ('email', 'success', 'ip_address', 'timestamp')
    list_filter = ('success', 'timestamp')
    search_fields = ('email', 'ip_address')
    date_hierarchy = 'timestamp'
    readonly_fields = ('timestamp',)


@admin.register(SecurityAlert)
class SecurityAlertAdmin(admin.ModelAdmin):
    list_display = ('alert_type', 'severity', 'ip_address', 'resolved', 'timestamp')
    list_filter = ('severity', 'alert_type', 'resolved')
    search_fields = ('description', 'ip_address')
    date_hierarchy = 'timestamp'
    readonly_fields = ('timestamp',)
    actions = ['mark_resolved']

    def mark_resolved(self, request, queryset):
        from django.utils import timezone
        queryset.update(resolved=True, resolved_at=timezone.now())
    mark_resolved.short_description = "Mark selected alerts as resolved"