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
        
        
class TeacherReview(models.Model):
    """
    Model for storing reviews given to teachers.
    """
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='reviews')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_reviews')
    rating = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review for {self.teacher} by {self.student}"
    
    
    
class ResearchPublication(models.Model):
    teacher = models.ForeignKey(
        Teacher, 
        on_delete=models.CASCADE,
        related_name="publications"
    )
    title = models.CharField(max_length=255)
    abstract = models.TextField()
    publication_date = models.DateField()
    journal_name = models.CharField(max_length=255, blank=True, null=True)
    doi_number = models.CharField(max_length=255, blank=True, null=True)
    pdf_file = models.FileField(upload_to="research_papers/", null=True, blank=True)

    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.teacher.user.get_full_name()})"

    class Meta:
        ordering = ["-publication_date"]