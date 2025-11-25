from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView

from .forms import TeacherForm, TeacherUserForm
from .models import Teacher
from students.views import AdminRequiredMixin

class TeacherListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    """View to list all teachers."""
    model = Teacher
    template_name = 'teachers/teacher_list.html'
    context_object_name = 'teachers'
    paginate_by = 10

class TeacherDetailView(LoginRequiredMixin, AdminRequiredMixin, DetailView):
    """View to display teacher details."""
    model = Teacher
    template_name = 'teachers/teacher_detail.html'
    context_object_name = 'teacher'

class TeacherCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    """View to create a new teacher."""
    template_name = 'teachers/teacher_form.html'
    success_url = reverse_lazy('teacher_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'user_form' not in context:
            context['user_form'] = TeacherUserForm()
        if 'teacher_form' not in context:
            context['teacher_form'] = TeacherForm()
        return context

    @transaction.atomic
    def form_valid(self, form):
        context = self.get_context_data()
        user_form = context['user_form']
        teacher_form = context['teacher_form']

        if user_form.is_valid() and teacher_form.is_valid():
            user = user_form.save(commit=False)
            user.user_type = 'teacher'
            user.save()

            teacher = teacher_form.save(commit=False)
            teacher.user = user
            teacher.save()

            return redirect(self.success_url)
        else:
            return self.render_to_response(self.get_context_data(user_form=user_form, teacher_form=teacher_form))

    def post(self, request, *args, **kwargs):
        self.object = None
        context = self.get_context_data()
        context['user_form'] = TeacherUserForm(request.POST)
        context['teacher_form'] = TeacherForm(request.POST)
        return self.form_valid(context)

class TeacherUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    """View to update teacher information."""
    model = Teacher
    form_class = TeacherForm
    template_name = 'teachers/teacher_form.html'
    success_url = reverse_lazy('teacher_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'user_form' not in context:
            context['user_form'] = TeacherUserForm(instance=self.object.user)
        return context

    @transaction.atomic
    def form_valid(self, form):
        context = self.get_context_data()
        user_form = context['user_form']

        if user_form.is_valid() and form.is_valid():
            user = user_form.save()
            teacher = form.save()
            return redirect(self.success_url)
        else:
            return self.render_to_response(self.get_context_data(user_form=user_form, form=form))

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data()
        context['user_form'] = TeacherUserForm(request.POST, instance=self.object.user)
        return super().post(request, *args, **kwargs)

class TeacherDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    """View to delete a teacher."""
    model = Teacher
    template_name = 'teachers/teacher_confirm_delete.html'
    success_url = reverse_lazy('teacher_list')

    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        teacher = self.get_object()
        user = teacher.user
        response = super().delete(request, *args, **kwargs)
        user.delete()
        return response