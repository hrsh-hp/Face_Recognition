from multiprocessing import Value
from django.contrib.auth.models import BaseUserManager


class UserManager(BaseUserManager):
    use_in_migrations = True
    
    def create_user(self, email, password, **extra_fields):
        if not  email:
            raise ValueError('Email is neccessary to create a user')
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using = self._db)
        return user
    
    
    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_staff',True)
        extra_fields.setdefault('is_superuser',True)
        
        if extra_fields.get('is_active') is not True:
            raise ValueError('Is_active must be True for superuser')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('User must be a staff as superuser')
        
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Super user must have Is-superuser true')
        
        
        return self.create_user(email, password, **extra_fields)