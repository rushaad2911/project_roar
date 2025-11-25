from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from django.shortcuts import render, redirect

from students.models import Student
from teachers.models import Teacher
from courses.models import Course, Enrollment
from attendance.models import AttendanceRecord, StudentAttendance
from fees.models import FeeInvoice, Payment

@login_required
def dashboard(request):
    """Main dashboard view that redirects to the appropriate dashboard based on user role."""
    if request.user.is_admin:
        return redirect('admin_dashboard')
    elif request.user.is_teacher:
        # Check if teacher profile exists
        try:
            Teacher.objects.get(user=request.user)
            return redirect('teacher_dashboard')
        except Teacher.DoesNotExist:
            # If no teacher profile, show a generic dashboard
            return render(request, 'dashboard/generic_dashboard.html', {
                'message': 'Your teacher profile is not set up yet. Please contact an administrator.'
            })
    elif request.user.is_student:
        # Check if student profile exists
        try:
            Student.objects.get(user=request.user)
            return redirect('student_dashboard')
        except Student.DoesNotExist:
            # If no student profile, show a generic dashboard
            return render(request, 'dashboard/generic_dashboard.html', {
                'message': 'Your student profile is not set up yet. Please contact an administrator.'
            })
    else:
        # For users with no specific role, show a generic dashboard
        return render(request, 'dashboard/generic_dashboard.html', {
            'message': 'Your account does not have a specific role assigned. Please contact an administrator.'
        })

@login_required
def admin_dashboard(request):
    """Dashboard view for administrators."""
    # Check if user is an admin
    if not request.user.is_admin:
        # If not an admin, redirect to the main dashboard
        return redirect('dashboard')

    # Get counts for various models
    student_count = Student.objects.count()
    teacher_count = Teacher.objects.count()
    course_count = Course.objects.count()
    enrollment_count = Enrollment.objects.count()

    # Get fee statistics
    total_fees = FeeInvoice.objects.aggregate(total=Sum('total_amount'))['total'] or 0
    total_paid = Payment.objects.aggregate(total=Sum('amount'))['total'] or 0
    total_pending = total_fees - total_paid

    # Get recent activities
    recent_enrollments = Enrollment.objects.order_by('-enrollment_date')[:5]
    recent_payments = Payment.objects.order_by('-payment_date')[:5]

    # Get attendance statistics
    attendance_stats = StudentAttendance.objects.values('status').annotate(count=Count('status'))

    context = {
        'student_count': student_count,
        'teacher_count': teacher_count,
        'course_count': course_count,
        'enrollment_count': enrollment_count,
        'total_fees': total_fees,
        'total_paid': total_paid,
        'total_pending': total_pending,
        'recent_enrollments': recent_enrollments,
        'recent_payments': recent_payments,
        'attendance_stats': attendance_stats,
    }

    return render(request, 'dashboard/admin_dashboard.html', context)

@login_required
def teacher_dashboard(request):
    """Dashboard view for teachers."""
    if not request.user.is_teacher:
        # If not a teacher, redirect to the main dashboard
        return redirect('dashboard')

    try:
        teacher = Teacher.objects.get(user=request.user)

        # Get courses taught by this teacher
        courses = teacher.courses.all()
        course_count = courses.count()

        # Get student counts for each course
        course_students = {}
        for course in courses:
            course_students[course] = Enrollment.objects.filter(course=course, status='active').count()

        # Get recent attendance records for teacher's courses
        recent_attendance = AttendanceRecord.objects.filter(course__in=courses).order_by('-date')[:5]

        context = {
            'teacher': teacher,
            'courses': courses,
            'course_count': course_count,
            'course_students': course_students,
            'recent_attendance': recent_attendance,
        }

        return render(request, 'dashboard/teacher_dashboard.html', context)

    except Teacher.DoesNotExist:
        # If teacher profile doesn't exist, show a generic dashboard
        return render(request, 'dashboard/generic_dashboard.html', {
            'message': 'Your teacher profile is not set up yet. Please contact an administrator.'
        })

@login_required
def student_dashboard(request):
    """Dashboard view for students."""
    if not request.user.is_student:
        # If not a student, redirect to the main dashboard
        return redirect('dashboard')

    try:
        student = Student.objects.get(user=request.user)

        # Get enrollments for this student
        enrollments = Enrollment.objects.filter(student=student, status='active')
        course_count = enrollments.count()

        # Get attendance statistics
        attendance_records = StudentAttendance.objects.filter(student=student)
        attendance_stats_raw = attendance_records.values('status').annotate(count=Count('status'))

        # Convert to a more template-friendly format
        attendance_stats = {
            'present': 0,
            'absent': 0,
            'late': 0,
            'excused': 0
        }

        for stat in attendance_stats_raw:
            attendance_stats[stat['status']] = stat['count']

        # Calculate attendance percentage
        total_attendance = sum(attendance_stats.values())
        present_percentage = 0
        if total_attendance > 0:
            present_percentage = (attendance_stats['present'] / total_attendance) * 100

        # Get fee information
        fee_invoices = FeeInvoice.objects.filter(student=student)
        total_fees = fee_invoices.aggregate(total=Sum('total_amount'))['total'] or 0
        total_paid = fee_invoices.aggregate(total=Sum('paid_amount'))['total'] or 0
        total_pending = total_fees - total_paid

        # Get recent attendance
        recent_attendance = attendance_records.order_by('-attendance_record__date')[:5]

        context = {
            'student': student,
            'enrollments': enrollments,
            'course_count': course_count,
            'attendance_stats': attendance_stats,
            'present_percentage': present_percentage,
            'total_fees': total_fees,
            'total_paid': total_paid,
            'total_pending': total_pending,
            'recent_attendance': recent_attendance,
        }

        return render(request, 'dashboard/student_dashboard.html', context)

    except Student.DoesNotExist:
        # If student profile doesn't exist, show a generic dashboard
        return render(request, 'dashboard/generic_dashboard.html', {
            'message': 'Your student profile is not set up yet. Please contact an administrator.'
        })