from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
class KnownFace(models.Model):
    name = models.CharField( max_length=250)
    image = models.TextField(default='none')
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

# class CustomeUser(AbstractUser):
    
#     phone_num = models.CharField(max_length=12,unique=True)
#     email = models.EmailField(unique= True, max_length=254)
#     user_image