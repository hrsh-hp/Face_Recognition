from django.urls import path
from .views import recognize_face,index,login_page,register,verify


app_name  = 'Auth'

urlpatterns = [
    path('',index,name='index'),
    path('face_recognize/',recognize_face,name='face_recognize'),
    path('login/',login_page,name="login_page"),
    path('register/', register,name="register"),
    path('verify/<email_token>',verify,name="verify"),
]
