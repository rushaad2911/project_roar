from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, UpdateView, DeleteView, DetailView,CreateView
from django.views import View
from django.db.models import Q, Avg

from .forms import *
from .models import Teacher, ResearchPublication
from students.views import AdminRequiredMixin
from department.models import Department
from .models import ResearchPublication
from django.core.exceptions import PermissionDenied
import requests
from django.urls import reverse


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



class TeacherDetailView(LoginRequiredMixin, DetailView):
    model = Teacher
    template_name = "teachers/teacher_detail.html"
    context_object_name = "teacher"
    def dispatch(self, request, *args, **kwargs):
        teacher = self.get_object()

        # Allow admin
        if request.user.is_admin:
            return super().dispatch(request, *args, **kwargs)

        # Allow teacher to see ONLY own profile
        if request.user.is_teacher and request.user == teacher.user:
            return super().dispatch(request, *args, **kwargs)

        # Deny everything else
        raise PermissionDenied("You cannot access this teacher profile.")

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
        
        publications = ResearchPublication.objects.filter(teacher=teacher)

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
            "publications": publications,


        })

        return context



class TeacherCreateView(LoginRequiredMixin, AdminRequiredMixin, View):
    template_name = "teachers/teacher_create.html"
    success_url = reverse_lazy("teacher_list")

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {
            "user_form": TeacherUserForm(),
            "teacher_form": TeacherForm(),
        })

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        user_form = TeacherUserForm(request.POST)
        teacher_form = TeacherForm(request.POST)

        if user_form.is_valid() and teacher_form.is_valid():
            # Create User
            user = user_form.save(commit=False)
            user.user_type = "teacher"
            user.save()

            # Create Teacher
            teacher = teacher_form.save(commit=False)
            teacher.user = user
            teacher.save()

            return redirect(self.success_url)

        return render(request, self.template_name, {
            "user_form": user_form,
            "teacher_form": teacher_form,
        })


class TeacherUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = Teacher
    form_class = TeacherForm
    template_name = "teachers/teacher_form.html"
    success_url = reverse_lazy("teacher_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user_form"] = TeacherUserForm(instance=self.object.user)
        return context

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        user_form = TeacherUserForm(request.POST, instance=self.object.user)
        teacher_form = TeacherForm(request.POST, instance=self.object)

        if user_form.is_valid() and teacher_form.is_valid():
            user_form.save()
            teacher_form.save()
            return redirect(self.success_url)

        return render(request, self.template_name, {
            "user_form": user_form,
            "teacher_form": teacher_form
        })

class TeacherDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    model = Teacher
    template_name = "teachers/teacher_confirm_delete.html"
    success_url = reverse_lazy("teacher_list")

    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        teacher = self.get_object()
        user = teacher.user
        teacher.delete()
        user.delete()
        return redirect(self.success_url)


class PublicationCreateView(LoginRequiredMixin, CreateView):
    model = ResearchPublication
    form_class = PublicationForm
    template_name = "teachers/publication_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.teacher = Teacher.objects.get(id=self.kwargs['teacher_id'])

        # Admin can add for anyone
        if request.user.is_admin:
            return super().dispatch(request, *args, **kwargs)

        # Teacher can add ONLY for themselves
        if request.user.is_teacher and request.user == self.teacher.user:
            return super().dispatch(request, *args, **kwargs)

        raise PermissionDenied("You cannot add a publication for this teacher.")

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, request.FILES)

        if form.is_valid():
            pub = form.save(commit=False)
            pub.teacher = self.teacher   # 🔥 FIXED — always set
            pub.save()
            return redirect("teacher_detail", pk=self.teacher.id)

        return render(request, self.template_name, {"form": form})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["teacher"] = self.teacher
        return context

class PublicationUpdateView(LoginRequiredMixin, UpdateView):
    model = ResearchPublication
    form_class = PublicationForm
    template_name = "teachers/publication_form.html"

    def get_success_url(self):
        return reverse_lazy("teacher_detail", kwargs={"pk": self.object.teacher.id})


class PublicationDeleteView(LoginRequiredMixin, DeleteView):
    model = ResearchPublication
    template_name = "teachers/publication_confirm_delete.html"

    def get_success_url(self):
        return reverse_lazy("teacher_detail", kwargs={"pk": self.object.teacher.id})
    
    
class PublicationListAdminView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = ResearchPublication
    template_name = "teachers/publication_list_admin.html"
    context_object_name = "publications"

    def get_queryset(self):
        return ResearchPublication.objects.select_related(
            "teacher", "teacher__user", "teacher__user__department"
        ).order_by("teacher__user__department__name", "teacher__user__first_name")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        grouped = {}   # { department: { teacher: [pubs] } }

        for pub in context["publications"]:
            dept = pub.teacher.user.department.name if pub.teacher.user.department else "No Department"
            teacher = pub.teacher

            if dept not in grouped:
                grouped[dept] = {}

            if teacher not in grouped[dept]:
                grouped[dept][teacher] = []

            grouped[dept][teacher].append(pub)

        context["grouped_publications"] = grouped
        return context

class PublicationListTeacherView(LoginRequiredMixin, ListView):
    model = ResearchPublication
    template_name = "teachers/publication_list_teacher.html"
    context_object_name = "publications"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_teacher:
            raise PermissionDenied("Only teachers can view their publications.")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return ResearchPublication.objects.filter(
            teacher=self.request.user.teacher_profile
        ).order_by("-publication_date")
