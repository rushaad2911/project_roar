from django import forms
from django.forms import inlineformset_factory
from .models import AttendanceRecord, StudentAttendance
from courses.models import Course, Enrollment

class AttendanceRecordForm(forms.ModelForm):
    """
    Form for creating and updating attendance records.
    """
    class Meta:
        model = AttendanceRecord
        fields = ['course', 'date']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to form fields
        for field_name, field in self.fields.items():
            if 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'

class StudentAttendanceForm(forms.ModelForm):
    """
    Form for creating and updating student attendance.
    """
    class Meta:
        model = StudentAttendance
        fields = ['student', 'status', 'remarks']
        widgets = {
            'remarks': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to form fields
        for field_name, field in self.fields.items():
            if 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'

# Create a formset for student attendance
StudentAttendanceFormSet = inlineformset_factory(
    AttendanceRecord, 
    StudentAttendance, 
    form=StudentAttendanceForm,
    extra=0,
    can_delete=False
)

class AttendanceFilterForm(forms.Form):
    """
    Form for filtering attendance records by course and date range.
    """
    course = forms.ModelChoiceField(
        queryset=Course.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
