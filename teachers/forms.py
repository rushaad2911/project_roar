from django import forms
from .models import Teacher,ResearchPublication
from accounts.models import User
from accounts.forms import CustomUserCreationForm


class TeacherUserForm(CustomUserCreationForm):
    """
    User form for creating a teacher, includes department selection.
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

        # Force teacher role
        self.initial['user_type'] = 'teacher'

        # Hide user_type
        if "user_type" in self.fields:
            self.fields['user_type'].widget = forms.HiddenInput()

        # Styling
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class TeacherForm(forms.ModelForm):
    """
    Teacher profile form.
    """
    class Meta:
        model = Teacher
        fields = [
            'teacher_id',
            'date_of_birth',
            'gender',
            'qualification',
            'experience',
            'salary'
        ]

        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')


class PublicationForm(forms.ModelForm):
    class Meta:
        model = ResearchPublication
        fields = [
            "title",
            "abstract",
            "publication_date",
            "journal_name",
            "doi_number",
            "pdf_file"
        ]
        widgets = {
            "publication_date": forms.DateInput(attrs={"type": "date"}),
            "abstract": forms.Textarea(attrs={"rows": 4}),
        }