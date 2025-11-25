from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """
    Custom User model for the Institute Management System.
    Extends Django's AbstractUser to add role-based access control.
    """
    USER_TYPE_CHOICES = (
        ('admin', 'Admin'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
    )
    
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='student')
    profile_pic = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    mobile = models.CharField(max_length=15, null=True, blank=True)
    
    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"
    
    @property
    def is_admin(self):
        return self.user_type == 'admin'
    
    @property
    def is_teacher(self):
        return self.user_type == 'teacher'
    
    @property
    def is_student(self):
        return self.user_type == 'student'
