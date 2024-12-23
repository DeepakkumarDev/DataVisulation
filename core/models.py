from django.contrib.auth.models import AbstractUser as BaseAbstractUser
from django.db import models

# Create your models here.

class User(BaseAbstractUser):
    email = models.EmailField(unique=True)
    

