from django.db import models

# Create your models here.
class KnownFace(models.Model):
    name = models.CharField( max_length=250)
    image = models.TextField(default='none')
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
