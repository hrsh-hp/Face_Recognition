from django.urls import path
from .views import recognize_face,index

urlpatterns = [
    path('',index,name='index'),
    path('face_recognize/',recognize_face,name='face_recognize'),
]
