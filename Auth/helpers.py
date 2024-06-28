from django.utils.html import strip_tags
from django.core.mail import send_mail,EmailMultiAlternatives
from django.conf import Settings

from Face_Recognition import settings

# def send_email_token(email, email_token):
#     try:
#         subject = "Verification Token for Face_recognition"
#         ngrok_link = get_ngrok_link()
#         # message = f"Click on this link to verify your email\n {ngrok_link}/Auth/verify/{email_token}"
#         html_content = """
#         <!DOCTYPE html>
#         <html lang="en">
#         <head>
#             <meta charset="UTF-8">
#             <meta name="viewport" content="width=device-width, initial-scale=1.0">
#             <title>Email and Password Form</title>
#             <style>
#                 body {
#                     font-family: Arial, sans-serif;
#                 }
#                 .container {
#                     max-width: 400px;
#                     margin: 0 auto;
#                     padding: 20px;
#                     border: 1px solid #ccc;
#                     border-radius: 5px;
#                 }
#                 .container h2 {
#                     text-align: center;
#                     margin-bottom: 20px;
#                 }
#                 .form-group {
#                     margin-bottom: 20px;
#                 }
#                 .form-group label {
#                     display: block;
#                     margin-bottom: 5px;
#                 }
#                 .form-group input[type="email"],
#                 .form-group input[type="password"] {
#                     width: 100%;
#                     padding: 10px;
#                     border: 1px solid #ccc;
#                     border-radius: 3px;
#                 }
#                 .form-group input[type="submit"] {
#                     background-color: #007bff;
#                     color: #fff;
#                     border: none;
#                     padding: 10px 20px;
#                     border-radius: 3px;
#                     cursor: pointer;
#                 }
#                 .form-group input[type="submit"]:hover {
#                     background-color: #0056b3;
#                 }
#             </style>
#         </head>
#         <body>
#             <div class="container">
#                 <h2>Login Form</h2>
#                 <form action="login.php" method="post">
#                     <div class="form-group">
#                         <label for="email">Email:</label>
#                         <input type="email" id="email" name="email" required>
#                     </div>
#                     <div class="form-group">
#                         <label for="password">Password:</label>
#                         <input type="password" id="password" name="password" required>
#                     </div>
#                     <div class="form-group">
#                         <input type="submit" value="Login">
#                     </div>
#                 </form>
#             </div>
#         </body>
#         </html>
#         """
#         email_from = settings.EMAIL_HOST_USER
#         recipient_list = [email]
#         email_send = EmailMultiAlternatives(subject,strip_tags(html_content), email_from, recipient_list)
#         email_send.attach_alternative(html_content, "text/html")
#         email_send.send()
#         return True
        
#     except Exception as e:
#         print(e)
#         return False

def send_email_token(email, email_token):
    try:
        subject = "Verification Token for Face_recognition"
        ngrok_link = get_ngrok_link()
        message = f"Click on this link to verify your email\n {ngrok_link}/Auth/verify/{email_token}"
        email_from = settings.EMAIL_HOST_USER
        recipient_list = [email]
        send_mail(subject, message, email_from, recipient_list)
        return True
        
    except Exception as e:
        print(e)
        return False
    
def get_ngrok_link():
    ngrok_link = " https://bd4e-152-59-33-145.ngrok-free.app"
    return ngrok_link if ngrok_link!="" else "127.0.0.1:8000"