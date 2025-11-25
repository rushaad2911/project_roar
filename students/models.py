from django.db import models
from accounts.models import User

class Student(models.Model):
    """
    Model for storing student-specific information.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    student_id = models.CharField(max_length=20, unique=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=(('male', 'Male'), ('female', 'Female'), ('other', 'Other')))
    parent_name = models.CharField(max_length=100, null=True, blank=True)
    parent_mobile = models.CharField(max_length=15, null=True, blank=True)
    admission_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} ({self.student_id})"

    class Meta:
        ordering = ['user__first_name', 'user__last_name']