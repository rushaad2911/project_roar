from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Sum, Avg
from django.shortcuts import render
from django.views.generic import TemplateView

from students.models import Student
from teachers.models import Teacher
from courses.models import Course, Enrollment
from attendance.models import AttendanceRecord, StudentAttendance
from fees.models import FeeInvoice, Payment
from students.views import AdminRequiredMixin

class ReportDashboardView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    """Main reports dashboard view."""
    template_name = 'reports/dashboard.html'

@login_required
def student_report(request):
    """View for generating student-related reports."""
    if not request.user.is_admin:
        return render(request, 'reports/access_denied.html')

    # Get student statistics
    total_students = Student.objects.count()
    students_by_gender = Student.objects.values('gender').annotate(count=Count('gender'))

    # Get enrollment statistics
    total_enrollments = Enrollment.objects.count()
    active_enrollments = Enrollment.objects.filter(status='active').count()
    completed_enrollments = Enrollment.objects.filter(status='completed').count()
    dropped_enrollments = Enrollment.objects.filter(status='dropped').count()

    context = {
        'total_students': total_students,
        'students_by_gender': students_by_gender,
        'total_enrollments': total_enrollments,
        'active_enrollments': active_enrollments,
        'completed_enrollments': completed_enrollments,
        'dropped_enrollments': dropped_enrollments,
    }

    return render(request, 'reports/student_report.html', context)

@login_required
def teacher_report(request):
    """View for generating teacher-related reports."""
    if not request.user.is_admin:
        return render(request, 'reports/access_denied.html')

    # Get teacher statistics
    total_teachers = Teacher.objects.count()
    teachers_by_gender = Teacher.objects.values('gender').annotate(count=Count('gender'))
    avg_experience = Teacher.objects.aggregate(avg_exp=Avg('experience'))['avg_exp'] or 0

    # Get course statistics per teacher
    teachers_with_courses = Teacher.objects.annotate(course_count=Count('courses'))

    context = {
        'total_teachers': total_teachers,
        'teachers_by_gender': teachers_by_gender,
        'avg_experience': avg_experience,
        'teachers_with_courses': teachers_with_courses,
    }

    return render(request, 'reports/teacher_report.html', context)

@login_required
def course_report(request):
    """View for generating course-related reports."""
    if not request.user.is_admin:
        return render(request, 'reports/access_denied.html')

    # Get course statistics
    total_courses = Course.objects.count()
    courses_with_students = Course.objects.annotate(student_count=Count('enrollments'))

    # Get enrollment statistics by course
    course_enrollments = {}
    for course in Course.objects.all():
        active = Enrollment.objects.filter(course=course, status='active').count()
        completed = Enrollment.objects.filter(course=course, status='completed').count()
        dropped = Enrollment.objects.filter(course=course, status='dropped').count()
        course_enrollments[course] = {
            'active': active,
            'completed': completed,
            'dropped': dropped,
            'total': active + completed + dropped
        }

    context = {
        'total_courses': total_courses,
        'courses_with_students': courses_with_students,
        'course_enrollments': course_enrollments,
    }

    return render(request, 'reports/course_report.html', context)

@login_required
def attendance_report(request):
    """View for generating attendance-related reports."""
    if not request.user.is_admin:
        return render(request, 'reports/access_denied.html')

    # Get attendance statistics
    total_records = AttendanceRecord.objects.count()
    attendance_by_status = StudentAttendance.objects.values('status').annotate(count=Count('status'))

    # Get attendance statistics by course
    course_attendance = {}
    for course in Course.objects.all():
        records = AttendanceRecord.objects.filter(course=course)
        if records.exists():
            present = StudentAttendance.objects.filter(attendance_record__course=course, status='present').count()
            absent = StudentAttendance.objects.filter(attendance_record__course=course, status='absent').count()
            late = StudentAttendance.objects.filter(attendance_record__course=course, status='late').count()
            excused = StudentAttendance.objects.filter(attendance_record__course=course, status='excused').count()
            total = present + absent + late + excused

            course_attendance[course] = {
                'present': present,
                'absent': absent,
                'late': late,
                'excused': excused,
                'total': total,
                'present_percentage': (present / total * 100) if total > 0 else 0
            }

    context = {
        'total_records': total_records,
        'attendance_by_status': attendance_by_status,
        'course_attendance': course_attendance,
    }

    return render(request, 'reports/attendance_report.html', context)

@login_required
def fee_report(request):
    """View for generating fee-related reports."""
    if not request.user.is_admin:
        return render(request, 'reports/access_denied.html')

    # Get fee statistics
    total_invoices = FeeInvoice.objects.count()
    total_amount = FeeInvoice.objects.aggregate(total=Sum('total_amount'))['total'] or 0
    total_paid = Payment.objects.aggregate(total=Sum('amount'))['total'] or 0
    total_pending = total_amount - total_paid

    # Get invoice statistics by status
    invoices_by_status = FeeInvoice.objects.values('status').annotate(count=Count('status'))

    # Get payment statistics by method
    payments_by_method = Payment.objects.values('payment_method').annotate(
        count=Count('payment_method'),
        total=Sum('amount')
    )

    context = {
        'total_invoices': total_invoices,
        'total_amount': total_amount,
        'total_paid': total_paid,
        'total_pending': total_pending,
        'invoices_by_status': invoices_by_status,
        'payments_by_method': payments_by_method,
    }

    return render(request, 'reports/fee_report.html', context)