from django import forms
from .models import Student
from accounts.models import User
from accounts.forms import CustomUserCreationForm

class StudentForm(forms.ModelForm):
    """
    Form for creating and updating student information.
    """
    class Meta:
        model = Student
        fields = ['student_id', 'date_of_birth', 'gender', 'parent_name', 'parent_mobile']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to form fields
        for field_name, field in self.fields.items():
            if 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'

class StudentUserForm(CustomUserCreationForm):
    """
    Combined form for creating a new user with student role and student profile.
    """
    class Meta(CustomUserCreationForm.Meta):
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set user_type to student by default
        self.initial['user_type'] = 'student'
        self.fields['user_type'].widget = forms.HiddenInput()
