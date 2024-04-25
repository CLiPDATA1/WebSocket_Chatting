# chat > models.py

from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager

class UserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError('The username must be set')
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self.create_user(username, password, **extra_fields)

class CustomUser(AbstractUser):
    dept_code = models.CharField(max_length=20)
    site_code = models.CharField(max_length=20) 
    
    objects = UserManager()
    
    REQUIRED_FIELDS = ['dept_code', 'site_code']
    
    def __str__(self):
        return self.username
    
class Message(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    message_type = models.CharField(max_length=20)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sent_messages', null=True)                
    
    def __str__(self):
        return self.message