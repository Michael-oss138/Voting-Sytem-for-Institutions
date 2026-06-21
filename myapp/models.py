from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('student', 'Student'),
        ('candidate', 'Candidate')
    )
    role       = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    matric_no  = models.CharField(max_length=20, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True)

    def save(self, *args, **kwargs):
        if self.is_superuser:
            self.role = 'admin'
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username


class Election(models.Model):
    STATUS_CHOICES = (
        ('draft',   'Draft'),
        ('opened',  'Opened'),
        ('closed',  'Closed'),
    )
    title                  = models.CharField(max_length=200)
    description            = models.TextField()
    start_time             = models.DateTimeField()
    end_time               = models.DateTimeField()
    status                 = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    created_by             = models.ForeignKey(User, on_delete=models.CASCADE)
    is_manually_controlled = models.BooleanField(default=False)

    def update_status(self):
        if self.is_manually_controlled:
            return
        now = timezone.now()
        if self.start_time <= now <= self.end_time:
            self.status = 'opened'
        elif now < self.start_time:
            self.status = 'draft'
        else:
            self.status = 'closed'
        self.save()

    def __str__(self):
        return self.title


class Post(models.Model):
    """A position/post within an election e.g. President, Fin Sec, PRO"""
    election    = models.ForeignKey(Election, on_delete=models.CASCADE, related_name='posts')
    title       = models.CharField(max_length=100)  # e.g. "President", "Fin Sec"
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.title} — {self.election.title}"


class Candidate(models.Model):
    STATUS_CHOICES = (
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    user       = models.ForeignKey(User, on_delete=models.CASCADE)
    election   = models.ForeignKey(Election, on_delete=models.CASCADE)
    post       = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='candidates')
    manifesto  = models.TextField()
    cgpa       = models.FloatField()
    department = models.CharField(max_length=100)
    status     = models.CharField(max_length=20, choices=STATUS_CHOICES, default='rejected')
    created_at = models.DateTimeField(auto_now_add=True)

    # AI Analysis fields
    ai_theme      = models.CharField(max_length=50, blank=True, null=True)
    ai_score      = models.CharField(max_length=20, blank=True, null=True)
    ai_confidence = models.FloatField(blank=True, null=True)


    class Meta:
        # A student can only apply once per post per election
        unique_together = ('user', 'election', 'post')

    def __str__(self):
        return f"{self.user.username} — {self.post.title} — {self.election.title}"


class Vote(models.Model):
    voter     = models.ForeignKey(User, on_delete=models.CASCADE)
    election  = models.ForeignKey(Election, on_delete=models.CASCADE)
    post      = models.ForeignKey(Post, on_delete=models.CASCADE)
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    voted_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        # A student can only vote once per post per election
        unique_together = ('voter', 'election', 'post')

    def __str__(self):
        return f"{self.voter.username} voted for {self.post.title} in {self.election.title}"