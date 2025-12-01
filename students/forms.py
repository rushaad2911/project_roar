from django import forms
from .models import Student
from accounts.models import User
from accounts.forms import CustomUserCreationForm


class StudentUserForm(CustomUserCreationForm):
    """
    User form for creating a student, includes department selection.
    """
    class Meta(CustomUserCreationForm.Meta):
        model = User
        fields = [
            'username',
            'first_name',
            'last_name',
            'email',
            'department',
            'password1',
            'password2'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.initial['user_type'] = 'student'

        # Hide user_type (we set it in backend)
        if 'user_type' in self.fields:
            self.fields['user_type'].widget = forms.HiddenInput()

        # Styling
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class StudentForm(forms.ModelForm):
    """
    Form for student profile fields.
    """
    class Meta:
        model = Student
        fields = [
            'student_id',
            'date_of_birth',
            'gender',
            'parent_name',
            'parent_mobile'
        ]

        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')
