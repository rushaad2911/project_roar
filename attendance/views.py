from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView

from .forms import AttendanceRecordForm, StudentAttendanceFormSet, AttendanceFilterForm
from .mixins import TeacherOrAdminRequiredMixin
from .models import AttendanceRecord, StudentAttendance
from courses.models import Course, Enrollment
from students.models import Student
from students.views import AdminRequiredMixin

class AttendanceRecordListView(LoginRequiredMixin, ListView):
    """View to list all attendance records."""
    model = AttendanceRecord
    template_name = 'attendance/attendance_record_list.html'
    context_object_name = 'attendance_records'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()

        # Apply filters if provided
        filter_form = AttendanceFilterForm(self.request.GET)
        if filter_form.is_valid():
            if filter_form.cleaned_data.get('course'):
                queryset = queryset.filter(course=filter_form.cleaned_data['course'])
            if filter_form.cleaned_data.get('start_date'):
                queryset = queryset.filter(date__gte=filter_form.cleaned_data['start_date'])
            if filter_form.cleaned_data.get('end_date'):
                queryset = queryset.filter(date__lte=filter_form.cleaned_data['end_date'])

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = AttendanceFilterForm(self.request.GET)
        context['courses'] = Course.objects.all()
        return context

class AttendanceRecordDetailView(LoginRequiredMixin, DetailView):
    """View to display attendance record details."""
    model = AttendanceRecord
    template_name = 'attendance/attendance_record_detail.html'
    context_object_name = 'attendance_record'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['student_attendances'] = self.object.student_attendances.all()
        context['present_count'] = self.object.get_present_count()
        context['absent_count'] = self.object.get_absent_count()
        context['late_count'] = self.object.get_late_count()
        context['excused_count'] = self.object.get_excused_count()
        return context

class AttendanceRecordCreateView(LoginRequiredMixin, TeacherOrAdminRequiredMixin, CreateView):
    """View to create a new attendance record."""
    model = AttendanceRecord
    form_class = AttendanceRecordForm
    template_name = 'attendance/attendance_record_form.html'
    success_url = reverse_lazy('attendance_record_list')

    def get_initial(self):
        initial = super().get_initial()
        # Check if course is provided in the URL
        course_id = self.request.GET.get('course')
        if course_id:
            try:
                initial['course'] = Course.objects.get(pk=course_id)
            except Course.DoesNotExist:
                pass
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get course from either POST data or GET parameter
        course_id = None

        if self.request.method == 'POST' and 'course' in self.request.POST:
            course_id = self.request.POST.get('course')
        elif 'course' in self.request.GET:
            course_id = self.request.GET.get('course')
        elif self.object and self.object.course_id:
            course_id = self.object.course_id

        # If we have a course ID, get the students
        if course_id:
            try:
                course = Course.objects.get(pk=course_id)
                # Get all active enrollments for this course
                enrollments = Enrollment.objects.filter(course=course, status='active')
                # Create a list of student data for the template
                students = []
                for enrollment in enrollments:
                    students.append({
                        'id': enrollment.student.id,
                        'name': enrollment.student.user.get_full_name(),
                        'student_id': enrollment.student.student_id
                    })
                context['students'] = students
                context['selected_course'] = course
            except Course.DoesNotExist:
                pass
        return context

    @transaction.atomic
    def form_valid(self, form):
        # Save the attendance record
        self.object = form.save()

        # Get all students enrolled in the course
        enrollments = Enrollment.objects.filter(
            course=self.object.course,
            status='active'
        )

        # Create attendance entries for each enrolled student
        for enrollment in enrollments:
            # Check if status was provided in the form
            student_id = str(enrollment.student.id)
            status_key = f'student_{student_id}_status'
            remarks_key = f'student_{student_id}_remarks'

            status = self.request.POST.get(status_key, 'present')
            remarks = self.request.POST.get(remarks_key, '')

            StudentAttendance.objects.create(
                attendance_record=self.object,
                student=enrollment.student,
                status=status,
                remarks=remarks
            )

        return redirect(self.get_success_url())

@login_required
def update_attendance(request, pk):
    """View to update student attendance for a specific attendance record."""
    # Check if user is admin or teacher
    if not (request.user.is_admin or request.user.is_teacher):
        return redirect('dashboard')
    attendance_record = get_object_or_404(AttendanceRecord, pk=pk)

    if request.method == 'POST':
        formset = StudentAttendanceFormSet(request.POST, instance=attendance_record)
        if formset.is_valid():
            formset.save()
            return redirect('attendance_record_detail', pk=attendance_record.pk)
    else:
        # If no student attendances exist, create them for all enrolled students
        if attendance_record.student_attendances.count() == 0:
            enrollments = Enrollment.objects.filter(
                course=attendance_record.course,
                status='active'
            )
            for enrollment in enrollments:
                StudentAttendance.objects.create(
                    attendance_record=attendance_record,
                    student=enrollment.student,
                    status='present'  # Default status
                )

        formset = StudentAttendanceFormSet(instance=attendance_record)

    return render(request, 'attendance/update_attendance.html', {
        'attendance_record': attendance_record,
        'formset': formset,
    })

class AttendanceRecordDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    """View to delete an attendance record."""
    model = AttendanceRecord
    template_name = 'attendance/attendance_record_confirm_delete.html'
    success_url = reverse_lazy('attendance_record_list')

class StudentAttendanceReportView(LoginRequiredMixin, ListView):
    """View for students to see their attendance records."""
    model = StudentAttendance
    template_name = 'attendance/student_attendance_report.html'
    context_object_name = 'attendances'

    def get_queryset(self):
        if self.request.user.is_student:
            student = Student.objects.filter(user=self.request.user).first()
            if student:
                return StudentAttendance.objects.filter(student=student)
        return StudentAttendance.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.user.is_student:
            student = Student.objects.filter(user=self.request.user).first()
            context['student'] = student

            if student:
                # Get attendance data
                attendances = StudentAttendance.objects.filter(student=student)

                total = attendances.count()
                present = attendances.filter(status='present').count()
                absent  = attendances.filter(status='absent').count()
                late    = attendances.filter(status='late').count()
                excused = attendances.filter(status='excused').count()

                context['total'] = total
                context['present'] = present
                context['absent'] = absent
                context['late'] = late
                context['excused'] = excused
                context['present_percentage'] = (present / total * 100) if total > 0 else 0

            else:
                # student does not exist → no crash, show empty UI
                context['total'] = 0
                context['present'] = 0
                context['absent'] = 0
                context['late'] = 0
                context['excused'] = 0
                context['present_percentage'] = 0

        return context
