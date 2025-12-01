from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction, models
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.db.models import Q, Avg

from .forms import TeacherForm, TeacherUserForm
from .models import Teacher
from students.views import AdminRequiredMixin
from department.models import Department


class TeacherListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = Teacher
    template_name = "teachers/teacher_list.html"
    context_object_name = "teachers"
    paginate_by = None

    def get_queryset(self):
        search = self.request.GET.get("q", "")
        dept_filter = self.request.GET.get("department", "all")

        qs = Teacher.objects.select_related("user", "user__department")

        if dept_filter != "all":
            qs = qs.filter(user__department_id=dept_filter)

        if search:
            qs = qs.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(user__email__icontains=search)
            )

        return qs.order_by("user__department__name", "user__first_name")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        dept_filter = self.request.GET.get("department", "all")
        search = self.request.GET.get("q", "")

        grouped = {}
        for t in context["teachers"]:
            dept = t.user.department.name if t.user.department else "No Department"
            grouped.setdefault(dept, []).append(t)

        context["departments"] = Department.objects.all()
        context["grouped_teachers"] = grouped
        context["selected_department"] = dept_filter
        context["search_query"] = search

        return context



class TeacherDetailView(LoginRequiredMixin, AdminRequiredMixin, DetailView):
    model = Teacher
    template_name = "teachers/teacher_detail.html"
    context_object_name = "teacher"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        teacher = self.object
        user = teacher.user

        # ================= COURSES ==================
        courses = teacher.courses.all()
        course_count = courses.count()

        from courses.models import Enrollment

        course_students = {
            course: Enrollment.objects.filter(course=course, status="active").count()
            for course in courses
        }

        # ================= ATTENDANCE ==================
        from attendance.models import AttendanceRecord, StudentAttendance

        attendance_stats = {
            "present": 0,
            "absent": 0,
            "late": 0,
            "excused": 0,
        }

        attendance_records = AttendanceRecord.objects.filter(course__in=courses)

        for record in attendance_records:
            rows = StudentAttendance.objects.filter(attendance_record=record)
            for r in rows:
                attendance_stats[r.status] += 1

        total_attendance = sum(attendance_stats.values())
        present_percentage = (
            attendance_stats["present"] * 100 / total_attendance
            if total_attendance > 0
            else 0
        )

        # ================= REVIEWS ==================
        reviews = teacher.reviews.select_related("student").order_by("-date_created")
        avg_rating = reviews.aggregate(rating=Avg("rating"))["rating"] or 0

        # ================= ADD TO CONTEXT ==================
        context.update({
            "teacher": teacher,
            "user": user,
            "courses": courses,
            "course_students": course_students,
            "course_count": course_count,
            "attendance_stats": attendance_stats,
            "present_percentage": present_percentage,
            "reviews": reviews,
            "avg_rating": avg_rating,
        })

        return context


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