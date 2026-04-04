from django.urls import path
from .views import (
    index, recognize_face, login_page, register,
    verify, logout_view, dashboard,
    api_access_logs, api_stats, resolve_alert
)

app_name = 'Auth'

urlpatterns = [
    path('', index, name='index'),
    path('face_recognize/', recognize_face, name='face_recognize'),
    path('login/', login_page, name='login_page'),
    path('register/', register, name='register'),
    path('verify/<str:email_token>', verify, name='verify'),
    path('logout/', logout_view, name='logout'),
    path('dashboard/', dashboard, name='dashboard'),
    path('api/access-logs/', api_access_logs, name='api_access_logs'),
    path('api/stats/', api_stats, name='api_stats'),
    path('api/alerts/<int:alert_id>/resolve/', resolve_alert, name='resolve_alert'),
]
