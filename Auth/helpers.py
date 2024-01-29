from csv import excel_tab
from django.core.mail import send_mail
from django.conf import Settings

from Face_Recognition import settings

def send_email_token(email, email_token):
    try:
        subject = "Verification Token for Face_recognition"
        message = f"Click on this link to verify your email\n http://127.0.0.1:8000/Auth/verify/{email_token}"
        email_from = settings.EMAIL_HOST_USER
        recipient_list = [email]
        send_mail(subject, message, email_from, recipient_list)
        return True
        
    except Exception as e:
        print(e)
        return False