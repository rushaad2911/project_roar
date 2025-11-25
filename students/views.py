from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView

from .forms import StudentForm, StudentUserForm
from .models import Student
from accounts.models import User

class AdminRequiredMixin(UserPassesTestMixin):
    """Mixin to ensure only admin users can access the view."""
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_admin

class StudentListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    """View to list all students."""
    model = Student
    template_name = 'students/student_list.html'
    context_object_name = 'students'
    paginate_by = 10

class StudentDetailView(LoginRequiredMixin, AdminRequiredMixin, DetailView):
    """View to display student details."""
    model = Student
    template_name = 'students/student_detail.html'
    context_object_name = 'student'

class StudentCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    """View to create a new student."""
    template_name = 'students/student_form.html'
    success_url = reverse_lazy('student_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'user_form' not in context:
            context['user_form'] = StudentUserForm()
        if 'student_form' not in context:
            context['student_form'] = StudentForm()
        return context

    @transaction.atomic
    def form_valid(self, form):
        context = self.get_context_data()
        user_form = context['user_form']
        student_form = context['student_form']

        if user_form.is_valid() and student_form.is_valid():
            user = user_form.save(commit=False)
            user.user_type = 'student'
            user.save()

            student = student_form.save(commit=False)
            student.user = user
            student.save()

            return redirect(self.success_url)
        else:
            return self.render_to_response(self.get_context_data(user_form=user_form, student_form=student_form))

    def post(self, request, *args, **kwargs):
        self.object = None
        context = self.get_context_data()
        context['user_form'] = StudentUserForm(request.POST)
        context['student_form'] = StudentForm(request.POST)
        return self.form_valid(context)

class StudentUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    """View to update student information."""
    model = Student
    form_class = StudentForm
    template_name = 'students/student_form.html'
    success_url = reverse_lazy('student_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'user_form' not in context:
            context['user_form'] = StudentUserForm(instance=self.object.user)
        return context

    @transaction.atomic
    def form_valid(self, form):
        context = self.get_context_data()
        user_form = context['user_form']

        if user_form.is_valid() and form.is_valid():
            user = user_form.save()
            student = form.save()
            return redirect(self.success_url)
        else:
            return self.render_to_response(self.get_context_data(user_form=user_form, form=form))

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data()
        context['user_form'] = StudentUserForm(request.POST, instance=self.object.user)
        return super().post(request, *args, **kwargs)

class StudentDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    """View to delete a student."""
    model = Student
    template_name = 'students/student_confirm_delete.html'
    success_url = reverse_lazy('student_list')

    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        student = self.get_object()
        user = student.user
        response = super().delete(request, *args, **kwargs)
        user.delete()
        return response