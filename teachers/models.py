from django.db import models
from accounts.models import User

class Teacher(models.Model):
    """
    Model for storing teacher-specific information.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    teacher_id = models.CharField(max_length=20, unique=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=(('male', 'Male'), ('female', 'Female'), ('other', 'Other')))
    qualification = models.CharField(max_length=100, null=True, blank=True)
    experience = models.PositiveIntegerField(default=0, help_text='Experience in years')
    date_joined = models.DateField(auto_now_add=True)
    salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} ({self.teacher_id})"

    class Meta:
        ordering = ['user__first_name', 'user__last_name']