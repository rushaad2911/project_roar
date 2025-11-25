from django.db import models
from courses.models import Course
from students.models import Student

class AttendanceRecord(models.Model):
    """
    Model for storing attendance records for a course on a specific date.
    """
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.course} - {self.date}"

    class Meta:
        unique_together = ['course', 'date']
        ordering = ['-date']

    def get_present_count(self):
        return self.student_attendances.filter(status='present').count()

    def get_absent_count(self):
        return self.student_attendances.filter(status='absent').count()

    def get_late_count(self):
        return self.student_attendances.filter(status='late').count()

    def get_excused_count(self):
        return self.student_attendances.filter(status='excused').count()

class StudentAttendance(models.Model):
    """
    Model for storing individual student attendance status.
    """
    STATUS_CHOICES = (
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('excused', 'Excused'),
    )

    attendance_record = models.ForeignKey(AttendanceRecord, on_delete=models.CASCADE, related_name='student_attendances')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance_records')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='present')
    remarks = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.student} - {self.attendance_record.date} - {self.get_status_display()}"

    class Meta:
        unique_together = ['attendance_record', 'student']
        ordering = ['student__user__first_name', 'student__user__last_name']