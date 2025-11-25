from django import forms
from .models import Course, Enrollment, Schedule

class CourseForm(forms.ModelForm):
    """
    Form for creating and updating course information.
    """
    class Meta:
        model = Course
        fields = ['name', 'code', 'description', 'credits', 'teachers']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'teachers': forms.SelectMultiple(attrs={'class': 'form-control select2'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to form fields
        for field_name, field in self.fields.items():
            if 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'

class ScheduleForm(forms.ModelForm):
    """
    Form for creating and updating course schedules.
    """
    class Meta:
        model = Schedule
        fields = ['day', 'start_time', 'end_time', 'room']
        widgets = {
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to form fields
        for field_name, field in self.fields.items():
            if 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'

class EnrollmentForm(forms.ModelForm):
    """
    Form for creating and updating student enrollments.
    """
    class Meta:
        model = Enrollment
        fields = ['student', 'course', 'status', 'grade']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to form fields
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'

class EnrollmentUpdateForm(forms.ModelForm):
    """
    Form for updating enrollment status and grade.
    """
    class Meta:
        model = Enrollment
        fields = ['status', 'grade']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to form fields
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
