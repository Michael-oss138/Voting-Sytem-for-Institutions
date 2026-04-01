from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('student', 'Student'),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    matric_no = models.CharField(max_length=20, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.username