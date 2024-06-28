from django.db import models
from django.contrib.auth.models import AbstractUser
from .managers import UserManager

# Create your models here.
class KnownFace(models.Model):
    name = models.CharField( max_length=250)
    image = models.TextField(default='none')
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class CustomUser(AbstractUser):
    
    username = None
    last_name = models.CharField(max_length=150, blank=True, null=True)
    phone_num = models.CharField(max_length=12,unique=True,null=True, blank=True)
    email = models.EmailField(unique= True, max_length=254)
    email_token = models.CharField(max_length=100, null=True, blank=True)
    is_email_verified = models.BooleanField(default=False)
    forgot_pass_token = models.CharField( max_length=100,null=True, blank=True)
    user_image = models.TextField(blank=True, null=True)
    register_date = models.DateTimeField(auto_now_add=True)
    enrollment = models.IntegerField(unique=True,null=True, blank=True)
    department = models.CharField(max_length=100, default="general")
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    objects = UserManager()
    
    def name(self):
        return self.first_name +" "+ self.last_name
    
    def __str__(self) -> str:
        return self.email
    
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .views import update_known_faces

@receiver(post_save, sender=CustomUser)
@receiver(post_delete, sender=CustomUser)
def update_known_faces_cache_on_change(sender, instance, **kwargs):
    update_known_faces()