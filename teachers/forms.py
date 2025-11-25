from django import forms
from .models import Teacher
from accounts.models import User
from accounts.forms import CustomUserCreationForm

class TeacherForm(forms.ModelForm):
    """
    Form for creating and updating teacher information.
    """
    class Meta:
        model = Teacher
        fields = ['teacher_id', 'date_of_birth', 'gender', 'qualification', 'experience', 'salary']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to form fields
        for field_name, field in self.fields.items():
            if 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'

class TeacherUserForm(CustomUserCreationForm):
    """
    Combined form for creating a new user with teacher role and teacher profile.
    """
    class Meta(CustomUserCreationForm.Meta):
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set user_type to teacher by default
        self.initial['user_type'] = 'teacher'
        self.fields['user_type'].widget = forms.HiddenInput()
