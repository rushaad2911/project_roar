from django.db import models
from teachers.models import Teacher
from students.models import Student
from department.models import Department

class Course(models.Model):
    """
    Model for storing course information.
    """
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(null=True, blank=True)
    credits = models.PositiveIntegerField(default=3)
    teachers = models.ManyToManyField(Teacher, related_name='courses')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, null=True, blank=True)


    def __str__(self):
        return f"{self.name} ({self.code})"

    class Meta:
        ordering = ['name']

class Enrollment(models.Model):
    """
    Model for storing student enrollments in courses.
    """
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('dropped', 'Dropped'),
    )

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrollment_date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    grade = models.CharField(max_length=2, null=True, blank=True)

    def __str__(self):
        return f"{self.student} - {self.course}"

    class Meta:
        unique_together = ['student', 'course']
        ordering = ['-enrollment_date']

class Schedule(models.Model):
    """
    Model for storing course schedules.
    """
    DAY_CHOICES = (
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
        ('sunday', 'Sunday'),
    )

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='schedules')
    day = models.CharField(max_length=10, choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    room = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return f"{self.course} - {self.get_day_display()} {self.start_time} to {self.end_time}"

    class Meta:
        ordering = ['day', 'start_time']