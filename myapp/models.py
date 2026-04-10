from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
# Create your models here.
class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('student', 'Student'),
        ('candidate', 'Candidate')
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    matric_no = models.CharField(max_length=20, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True)

    def save(self, *args, **kwargs):
        if self.is_superuser:
            self.role = 'admin'
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username

class Election(models.Model):
    STATUS_CHOICES =(
        ('draft', 'Draft'),
        ('opened', 'Opened'),
        ('closed', 'Closed')
    )

    title = models.CharField(max_length=200)
    description = models.TextField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')

    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    is_manually_controlled = models.BooleanField(default=False)

    def update_status(self):
        if self.is_manually_controlled:
            return
        
        now = timezone.now()

        if self.start_time <=now <= self.end_time:
            self.status = 'opened'
        elif now < self.start_time:
            self.status = 'closed'
        else:
            self.status = 'draft'

            self.save()
    def __str__(self):
        return self.title


    