from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.shortcuts import redirect
from django.db import transaction
from django.urls import reverse_lazy
from django.db.models import Q
from django.shortcuts import render, redirect

from .models import Student
from .forms import StudentForm, StudentUserForm
from accounts.models import User
from django.views import View


class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_admin


class StudentListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = Student
    template_name = 'students/student_list.html'
    context_object_name = 'students'
    paginate_by = None

    def get_queryset(self):
        search = self.request.GET.get("q", "")
        dept_filter = self.request.GET.get("department", "all")

        qs = Student.objects.select_related("user", "user__department")

        # Filter by department
        if dept_filter != "all":
            qs = qs.filter(user__department__id=dept_filter)

        # Search filter
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

        # Group students when "all"
        grouped = {}
        for s in context["students"]:
            dept = s.user.department.name if s.user.department else "No Department"
            grouped.setdefault(dept, []).append(s)

        from department.models import Department
        context["departments"] = Department.objects.all()

        context["grouped_students"] = grouped
        context["selected_department"] = dept_filter
        context["search_query"] = search
        return context



class StudentDetailView(LoginRequiredMixin, AdminRequiredMixin, DetailView):
    model = Student
    template_name = 'students/student_detail.html'
    context_object_name = 'student'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.object

        from courses.models import Enrollment
        from attendance.models import StudentAttendance
        from fees.models import FeeInvoice

        # Enrollments
        enrollments = Enrollment.objects.filter(student=student)
        context["enrollments"] = enrollments
        context["course_count"] = enrollments.count()

        # Attendance statistics
        attendance_records = StudentAttendance.objects.filter(student=student)

        attendance_stats = {
            "present": attendance_records.filter(status="present").count(),
            "absent": attendance_records.filter(status="absent").count(),
            "late": attendance_records.filter(status="late").count(),
            "excused": attendance_records.filter(status="excused").count(),
        }
        context["attendance_stats"] = attendance_stats

        total = sum(attendance_stats.values())
        context["present_percentage"] = (attendance_stats["present"] / total * 100) if total > 0 else 0

        # Recent attendance
        context["recent_attendance"] = attendance_records.order_by('-attendance_record__date')[:5]

        # Fee Summary
        from django.db.models import Sum
        invoices = FeeInvoice.objects.filter(student=student)

        total_fees = invoices.aggregate(t=Sum("total_amount"))["t"] or 0
        total_paid = invoices.aggregate(t=Sum("paid_amount"))["t"] or 0

        context["total_fees"] = total_fees
        context["total_paid"] = total_paid
        context["total_pending"] = total_fees - total_paid

        return context


class StudentCreateView(LoginRequiredMixin, AdminRequiredMixin, View):
    template_name = 'students/student_form.html'
    success_url = reverse_lazy('student_list')

    def get(self, request, *args, **kwargs):
        user_form = StudentUserForm()
        student_form = StudentForm()
        return render(request, self.template_name, {
            "user_form": user_form,
            "student_form": student_form,
        })

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        user_form = StudentUserForm(request.POST)
        student_form = StudentForm(request.POST)

        if user_form.is_valid() and student_form.is_valid():

            # Create user
            user = user_form.save(commit=False)
            user.user_type = "student"
            user.save()

            # Create student
            student = student_form.save(commit=False)
            student.user = user
            student.save()

            return redirect(self.success_url)

        return render(request, self.template_name, {
            "user_form": user_form,
            "student_form": student_form,
        })


class StudentUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = Student
    form_class = StudentForm
    template_name = 'students/student_form.html'
    success_url = reverse_lazy('student_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.setdefault('user_form', StudentUserForm(instance=self.object.user))
        return context

    @transaction.atomic
    def form_valid(self, form):
        user_form = self.get_context_data()['user_form']

        if user_form.is_valid() and form.is_valid():
            user_form.save()
            form.save()
            return redirect(self.success_url)

        return self.render_to_response(self.get_context_data(form=form))


class StudentDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
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
