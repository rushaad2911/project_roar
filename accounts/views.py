from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView

from .forms import CustomUserCreationForm, CustomAuthenticationForm, UserProfileForm
from .models import User

class CustomLoginView(LoginView):
    """
    Custom login view using the CustomAuthenticationForm.
    """
    form_class = CustomAuthenticationForm
    template_name = 'accounts/login.html'

    def get_success_url(self):
        """Redirect users based on their role."""
        # Simply redirect to the main dashboard view which will handle role-specific redirects
        return reverse_lazy('dashboard')

class RegisterView(CreateView):
    """
    View for user registration.
    """
    model = User
    form_class = CustomUserCreationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('login')

@login_required
def profile_view(request):
    """
    View for displaying and updating user profile.
    """
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            # Add a success message
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=request.user)

    return render(request, 'accounts/profile.html', {'form': form})

def logout_view(request):
    """
    View for user logout.
    """
    logout(request)
    return redirect('login')
