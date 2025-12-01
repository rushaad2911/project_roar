from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Sum, Avg
from django.shortcuts import render
from django.views.generic import TemplateView
from django.http import HttpResponse
from django.views import View

from students.models import Student
from teachers.models import Teacher
from courses.models import Course, Enrollment
from attendance.models import AttendanceRecord, StudentAttendance
from fees.models import FeeInvoice, Payment
from students.views import AdminRequiredMixin

from openpyxl import Workbook
from openpyxl.utils import get_column_letter

import matplotlib
matplotlib.use("Agg")  # non-GUI backend
import matplotlib.pyplot as plt

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader

import io


# ----------------------------------------------------
#  📌 DASHBOARD VIEW
# ----------------------------------------------------

class ReportDashboardView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    template_name = 'reports/dashboard.html'


# ----------------------------------------------------
#  📌 NORMAL HTML REPORT VIEWS
# ----------------------------------------------------

@login_required
def student_report(request):
    if not request.user.is_admin:
        return render(request, 'reports/access_denied.html')

    total_students = Student.objects.count()
    students_by_gender = Student.objects.values("gender").annotate(count=Count("id"))

    total_enrollments = Enrollment.objects.count()
    active_enrollments = Enrollment.objects.filter(status="active").count()
    completed_enrollments = Enrollment.objects.filter(status="completed").count()
    dropped_enrollments = Enrollment.objects.filter(status="dropped").count()

    context = {
        "total_students": total_students,
        "students_by_gender": students_by_gender,
        "total_enrollments": total_enrollments,
        "active_enrollments": active_enrollments,
        "completed_enrollments": completed_enrollments,
        "dropped_enrollments": dropped_enrollments,
    }

    return render(request, 'reports/student_report.html', context)


@login_required
def teacher_report(request):
    if not request.user.is_admin:
        return render(request, 'reports/access_denied.html')

    total_teachers = Teacher.objects.count()
    teachers_by_gender = Teacher.objects.values("gender").annotate(count=Count("id"))
    avg_experience = Teacher.objects.aggregate(ex=Avg("experience"))["ex"] or 0
    teachers_with_courses = Teacher.objects.annotate(course_count=Count("courses"))

    context = {
        "total_teachers": total_teachers,
        "teachers_by_gender": teachers_by_gender,
        "avg_experience": avg_experience,
        "teachers_with_courses": teachers_with_courses,
    }

    return render(request, 'reports/teacher_report.html', context)


@login_required
def course_report(request):
    if not request.user.is_admin:
        return render(request, 'reports/access_denied.html')

    total_courses = Course.objects.count()
    courses_with_students = Course.objects.annotate(student_count=Count("enrollments"))

    course_enrollments = {}
    for course in Course.objects.all():
        active = Enrollment.objects.filter(course=course, status="active").count()
        completed = Enrollment.objects.filter(course=course, status="completed").count()
        dropped = Enrollment.objects.filter(course=course, status="dropped").count()
        course_enrollments[course] = {
            "active": active,
            "completed": completed,
            "dropped": dropped,
            "total": active + completed + dropped
        }

    context = {
        "total_courses": total_courses,
        "courses_with_students": courses_with_students,
        "course_enrollments": course_enrollments,
    }
    return render(request, 'reports/course_report.html', context)


@login_required
def attendance_report(request):
    if not request.user.is_admin:
        return render(request, 'reports/access_denied.html')

    total_records = AttendanceRecord.objects.count()
    attendance_by_status = StudentAttendance.objects.values("status").annotate(count=Count("id"))

    course_attendance = {}
    for course in Course.objects.all():
        records = StudentAttendance.objects.filter(attendance_record__course=course)
        if records.exists():
            pres = records.filter(status="present").count()
            absn = records.filter(status="absent").count()
            late = records.filter(status="late").count()
            exc = records.filter(status="excused").count()
            tot = pres + absn + late + exc
            course_attendance[course] = {
                "present": pres,
                "absent": absn,
                "late": late,
                "excused": exc,
                "total": tot,
                "present_percentage": (pres / tot * 100) if tot else 0,
            }

    context = {
        "total_records": total_records,
        "attendance_by_status": attendance_by_status,
        "course_attendance": course_attendance,
    }

    return render(request, 'reports/attendance_report.html', context)


@login_required
def fee_report(request):
    if not request.user.is_admin:
        return render(request, 'reports/access_denied.html')

    total_invoices = FeeInvoice.objects.count()
    total_amount = FeeInvoice.objects.aggregate(t=Sum("total_amount"))["t"] or 0
    total_paid = Payment.objects.aggregate(p=Sum("amount"))["p"] or 0
    total_pending = total_amount - total_paid

    invoices_by_status = FeeInvoice.objects.values("status").annotate(count=Count("id"))
    payments_by_method = Payment.objects.values("payment_method").annotate(
        count=Count("id"), total=Sum("amount")
    )

    context = {
        "total_invoices": total_invoices,
        "total_amount": total_amount,
        "total_paid": total_paid,
        "total_pending": total_pending,
        "invoices_by_status": invoices_by_status,
        "payments_by_method": payments_by_method,
    }
    return render(request, 'reports/fee_report.html', context)


# ----------------------------------------------------
#  📌 XLS EXPORT (Teacher)
# ----------------------------------------------------

class TeacherXLSDownload(View):
    def get(self, request, *args, **kwargs):
        if not request.user.is_admin:
            return HttpResponse("Not authorized")

        wb = Workbook()
        ws = wb.active
        ws.title = "Teacher Report"

        headers = ["Teacher Name", "Gender", "Experience", "Courses"]
        ws.append(headers)

        teachers = Teacher.objects.annotate(course_count=Count("courses"))

        for t in teachers:
            ws.append([
                t.user.get_full_name() or t.user.username,
                t.gender,
                t.experience,
                t.course_count
            ])

        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = 'attachment; filename="Teacher_Report.xlsx"'

        wb.save(response)
        return response


# ----------------------------------------------------
#  📌 UTIL – CHART IMAGE GENERATOR
# ----------------------------------------------------

def chart_image(plot_fn):
    """
    Helper to create a matplotlib chart and return an ImageReader
    usable by ReportLab.
    """
    buf = io.BytesIO()
    plt.figure(figsize=(6, 4))
    plot_fn()
    plt.tight_layout()
    plt.savefig(buf, format="png")
    plt.close()
    buf.seek(0)
    return ImageReader(buf)


# ----------------------------------------------------
#  📌 STUDENT PDF – MATCHES DASHBOARD CHARTS
# ----------------------------------------------------

@login_required
def student_report_pdf(request):
    if not request.user.is_admin:
        return HttpResponse("Not authorized", status=403)

    # ---------- DATA ----------
    total_students = Student.objects.count()
    students_by_gender = Student.objects.values("gender").annotate(count=Count("id"))

    active = Enrollment.objects.filter(status="active").count()
    completed = Enrollment.objects.filter(status="completed").count()
    dropped = Enrollment.objects.filter(status="dropped").count()
    total_enrollments = active + completed + dropped

    active_percent = (active / total_enrollments * 100) if total_enrollments else 0

    # Example top courses (placeholder – you can replace with real query later)
    sample_course_labels = ["Course A", "Course B", "Course C", "Course D", "Course E"]
    sample_course_values = [40, 32, 27, 20, 10]

    # ---------- CHARTS ----------

    gender_chart = chart_image(lambda: (
        plt.pie(
            [g["count"] for g in students_by_gender],
            labels=[g["gender"] for g in students_by_gender],
            autopct="%1.1f%%"
        ),
        plt.title("Gender Distribution")
    ))

    enrollment_breakdown_chart = chart_image(lambda: (
        plt.bar(["Active", "Completed", "Dropped"], [active, completed, dropped]),
        plt.title("Enrollments Breakdown")
    ))

    trend_chart = chart_image(lambda: (
        plt.plot(["Active", "Completed", "Dropped"], [active, completed, dropped], marker="o"),
        plt.grid(True),
        plt.title("Enrollment Trend")
    ))

    course_popularity_chart = chart_image(lambda: (
        plt.bar(sample_course_labels, sample_course_values),
        plt.xticks(rotation=45, ha="right"),
        plt.title("Top Courses by Enrollment")
    ))

    completion_drop_chart = chart_image(lambda: (
        plt.bar(["Completed", "Dropped"], [completed, dropped]),
        plt.title("Completion vs Drop")
    ))

    active_percent_chart = chart_image(lambda: (
        plt.pie(
            [active_percent, 100 - active_percent if active_percent <= 100 else 0],
            labels=["Active %", "Remaining %"],
            autopct="%1.1f%%"
        ),
        plt.title("Active Enrollment Percentage")
    ))

    # ---------- PDF BUILD ----------

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="Student_Report.pdf"'
    c = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    # PAGE 1 – Summary + Gender chart
    c.setFont("Helvetica-Bold", 20)
    c.drawString(40, height - 40, "Student Report")

    c.setFont("Helvetica", 12)
    c.drawString(40, height - 80, f"Total Students: {total_students}")
    c.drawString(40, height - 100, f"Active Enrollments: {active}")
    c.drawString(40, height - 120, f"Completed Enrollments: {completed}")
    c.drawString(40, height - 140, f"Dropped Enrollments: {dropped}")

    c.drawImage(gender_chart, 40, height - 450, width=300, height=300)
    c.showPage()

    # PAGE 2 – Enrollments breakdown + trend
    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, height - 40, "Enrollment Overview")

    c.drawImage(enrollment_breakdown_chart, 40, height - 300, width=500, height=250)
    c.drawImage(trend_chart, 40, height - 600, width=500, height=250)
    c.showPage()

    # PAGE 3 – Top courses + completion vs drop
    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, height - 40, "Course Analysis")

    c.drawImage(course_popularity_chart, 40, height - 300, width=500, height=250)
    c.drawImage(completion_drop_chart, 40, height - 600, width=500, height=250)
    c.showPage()

    # PAGE 4 – Active %
    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, height - 40, "Active Enrollment Percentage")

    c.drawImage(active_percent_chart, 120, height - 400, width=350, height=350)
    c.showPage()

    c.save()
    return response

# ----------------------------------------------------
#  📌 TEACHER PDF – FULL MULTI-PAGE REPORT
# ----------------------------------------------------

@login_required
def teacher_report_pdf(request):
    if not request.user.is_admin:
        return HttpResponse("Not authorized", status=403)

    # ------------------ DATA ------------------
    teachers = Teacher.objects.annotate(course_count=Count("courses"))
    teachers_by_gender = Teacher.objects.values("gender").annotate(count=Count("id"))
    total_teachers = teachers.count()
    avg_experience = teachers.aggregate(avg=Avg("experience"))["avg"] or 0

    # Top teachers (by courses assigned)
    top_teachers = sorted(teachers, key=lambda t: t.course_count, reverse=True)[:5]

    # ------------------ CHARTS ------------------

    gender_chart = chart_image(lambda: (
        plt.pie(
            [g["count"] for g in teachers_by_gender],
            labels=[g["gender"] for g in teachers_by_gender],
            autopct="%1.1f%%"
        ),
        plt.title("Teacher Gender Distribution")
    ))

    exp_chart = chart_image(lambda: (
        plt.bar(
            [t.user.get_full_name() or t.user.username for t in teachers],
            [t.experience for t in teachers]
        ),
        plt.xticks(rotation=45, ha="right"),
        plt.title("Experience (Years)")
    ))

    course_load_chart = chart_image(lambda: (
        plt.bar(
            [t.user.get_full_name() or t.user.username for t in teachers],
            [t.course_count for t in teachers]
        ),
        plt.xticks(rotation=45, ha="right"),
        plt.title("Courses Assigned per Teacher")
    ))

    top_teacher_chart = chart_image(lambda: (
        plt.bar(
            [t.user.get_full_name() or t.user.username for t in top_teachers],
            [t.course_count for t in top_teachers],
            color="green"
        ),
        plt.xticks(rotation=45, ha="right"),
        plt.title("Top 5 Teachers by Course Load")
    ))

    avg_exp_chart = chart_image(lambda: (
        plt.bar(["Average Experience"], [avg_experience]),
        plt.title("Average Experience (Years)")
    ))

    # ------------------ PDF BUILD ------------------

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename=\"Teacher_Report.pdf\"'
    c = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    # PAGE 1 – SUMMARY + Gender Chart
    c.setFont("Helvetica-Bold", 20)
    c.drawString(40, height - 40, "Teacher Report Summary")

    c.setFont("Helvetica", 12)
    c.drawString(40, height - 80, f"Total teachers: {total_teachers}")
    c.drawString(40, height - 100, f"Average experience: {avg_experience:.1f} years")

    c.drawImage(gender_chart, 40, height - 450, width=300, height=300)
    c.showPage()

    # PAGE 2 – Teachers Experience Distribution
    c.setFont("Helvetica-Bold", 18)
    c.drawString(40, height - 40, "Experience Distribution")

    c.drawImage(exp_chart, 40, height - 380, width=500, height=300)
    c.showPage()

    # PAGE 3 – Course Load per Teacher
    c.setFont("Helvetica-Bold", 18)
    c.drawString(40, height - 40, "Course Load Overview")

    c.drawImage(course_load_chart, 40, height - 380, width=500, height=300)
    c.showPage()

    # PAGE 4 – Top 5 Teachers
    c.setFont("Helvetica-Bold", 18)
    c.drawString(40, height - 40, "Top 5 Teachers (Course Load)")

    c.drawImage(top_teacher_chart, 40, height - 380, width=500, height=300)
    c.showPage()

    # PAGE 5 – Average Experience
    c.setFont("Helvetica-Bold", 18)
    c.drawString(40, height - 40, "Average Experience Summary")

    c.drawImage(avg_exp_chart, 120, height - 350, width=300, height=300)
    c.showPage()

    c.save()
    return response


# ----------------------------------------------------
#  📌 COURSE PDF – MULTI-PAGE REPORT
# ----------------------------------------------------

@login_required
def course_report_pdf(request):
    if not request.user.is_admin:
        return HttpResponse("Not authorized", status=403)

    courses = Course.objects.annotate(student_count=Count("enrollments"))
    total_courses = courses.count()

    # ----- Chart 1: Students per course -----
    chart_students = chart_image(lambda: (
        plt.bar(
            [c.name for c in courses],
            [c.student_count for c in courses]
        ),
        plt.xticks(rotation=45, ha="right"),
        plt.title("Students Per Course")
    ))

    # ----- Chart 2: Active enrollments per course -----
    active_counts = [
        Enrollment.objects.filter(course=c, status="active").count()
        for c in courses
    ]

    chart_active = chart_image(lambda: (
        plt.bar(
            [c.name for c in courses],
            active_counts,
            color="green"
        ),
        plt.xticks(rotation=45, ha="right"),
        plt.title("Active Enrollments Per Course")
    ))

    # ----- Chart 3: Completed enrollments per course -----
    completed_counts = [
        Enrollment.objects.filter(course=c, status="completed").count()
        for c in courses
    ]

    chart_completed = chart_image(lambda: (
        plt.bar(
            [c.name for c in courses],
            completed_counts,
            color="blue"
        ),
        plt.xticks(rotation=45, ha="right"),
        plt.title("Completed Enrollments Per Course")
    ))

    # ----- Chart 4: Dropped enrollments per course -----
    dropped_counts = [
        Enrollment.objects.filter(course=c, status="dropped").count()
        for c in courses
    ]

    chart_dropped = chart_image(lambda: (
        plt.bar(
            [c.name for c in courses],
            dropped_counts,
            color="red"
        ),
        plt.xticks(rotation=45, ha="right"),
        plt.title("Dropped Enrollments Per Course")
    ))

    # ------------------ PDF ---------------------
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="Course_Report.pdf"'
    c = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    # PAGE 1 – Summary
    c.setFont("Helvetica-Bold", 20)
    c.drawString(40, height - 40, "Course Report")

    c.setFont("Helvetica", 12)
    c.drawString(40, height - 80, f"Total Courses: {total_courses}")

    c.drawImage(chart_students, 40, height - 450, width=500, height=350)
    c.showPage()

    # PAGE 2 – Active
    c.setFont("Helvetica-Bold", 18)
    c.drawString(40, height - 40, "Active Enrollments Per Course")

    c.drawImage(chart_active, 40, height - 450, width=500, height=350)
    c.showPage()

    # PAGE 3 – Completed
    c.setFont("Helvetica-Bold", 18)
    c.drawString(40, height - 40, "Completed Enrollments Per Course")

    c.drawImage(chart_completed, 40, height - 450, width=500, height=350)
    c.showPage()

    # PAGE 4 – Dropped
    c.setFont("Helvetica-Bold", 18)
    c.drawString(40, height - 40, "Dropped Enrollments Per Course")

    c.drawImage(chart_dropped, 40, height - 450, width=500, height=350)
    c.showPage()

    c.save()
    return response

# ----------------------------------------------------
#  📌 ATTENDANCE PDF – MULTI-PAGE REPORT
# ----------------------------------------------------

@login_required
def attendance_report_pdf(request):
    if not request.user.is_admin:
        return HttpResponse("Not authorized", status=403)

    attendance_status = StudentAttendance.objects.values("status").annotate(count=Count("id"))

    # ----- Chart 1: Overall attendance pie -----
    chart_overall = chart_image(lambda: (
        plt.pie(
            [x["count"] for x in attendance_status],
            labels=[x["status"] for x in attendance_status],
            autopct="%1.1f%%"
        ),
        plt.title("Attendance Status Overview")
    ))

    # ----- Chart 2: Present only -----
    present = next((x["count"] for x in attendance_status if x["status"] == "present"), 0)
    chart_present = chart_image(lambda: (
        plt.bar(["Present"], [present], color="green"),
        plt.title("Total Present")
    ))

    # ----- Chart 3: Absent only -----
    absent = next((x["count"] for x in attendance_status if x["status"] == "absent"), 0)
    chart_absent = chart_image(lambda: (
        plt.bar(["Absent"], [absent], color="red"),
        plt.title("Total Absent")
    ))

    # ----- Chart 4: Late -----
    late = next((x["count"] for x in attendance_status if x["status"] == "late"), 0)
    chart_late = chart_image(lambda: (
        plt.bar(["Late"], [late], color="orange"),
        plt.title("Total Late")
    ))

    # ----- Chart 5: Excused -----
    excused = next((x["count"] for x in attendance_status if x["status"] == "excused"), 0)
    chart_excused = chart_image(lambda: (
        plt.bar(["Excused"], [excused], color="blue"),
        plt.title("Total Excused")
    ))

    # ------------------ PDF -------------------
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="Attendance_Report.pdf"'
    c = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    # PAGE 1 – Overview Pie Chart
    c.setFont("Helvetica-Bold", 20)
    c.drawString(40, height - 40, "Attendance Report")
    c.drawImage(chart_overall, 40, height - 450, width=400, height=350)
    c.showPage()

    # PAGE 2 – Present Count
    c.setFont("Helvetica-Bold", 18)
    c.drawString(40, height - 40, "Present Records")
    c.drawImage(chart_present, 150, height - 350, width=280, height=250)
    c.showPage()

    # PAGE 3 – Absent Count
    c.setFont("Helvetica-Bold", 18)
    c.drawString(40, height - 40, "Absent Records")
    c.drawImage(chart_absent, 150, height - 350, width=280, height=250)
    c.showPage()

    # PAGE 4 – Late Count
    c.setFont("Helvetica-Bold", 18)
    c.drawString(40, height - 40, "Late Records")
    c.drawImage(chart_late, 150, height - 350, width=280, height=250)
    c.showPage()

    # PAGE 5 – Excused Count
    c.setFont("Helvetica-Bold", 18)
    c.drawString(40, height - 40, "Excused Records")
    c.drawImage(chart_excused, 150, height - 350, width=280, height=250)
    c.showPage()

    c.save()
    return response

# ----------------------------------------------------
#  📌 FEES REPORT PDF – MULTI-PAGE REPORT
# ----------------------------------------------------

@login_required
def fee_report_pdf(request):
    if not request.user.is_admin:
        return HttpResponse("Not authorized", status=403)

    # -------- DATA --------
    total_amount = FeeInvoice.objects.aggregate(t=Sum("total_amount"))["t"] or 0
    total_paid = Payment.objects.aggregate(p=Sum("amount"))["p"] or 0
    pending_amount = total_amount - total_paid

    invoice_status = FeeInvoice.objects.values("status").annotate(count=Count("id"))
    payments_by_method = Payment.objects.values("payment_method").annotate(
        count=Count("id"), total=Sum("amount")
    )

    # -------- CHART 1 – Fee Summary Pie --------
    chart_summary = chart_image(lambda: (
        plt.pie(
            [total_paid, pending_amount],
            labels=["Paid", "Pending"],
            autopct="%1.1f%%",
            colors=["green", "red"]
        ),
        plt.title("Fees Summary Breakdown")
    ))

    # -------- CHART 2 – Invoice Status --------
    chart_status = chart_image(lambda: (
        plt.bar(
            [s["status"] for s in invoice_status],
            [s["count"] for s in invoice_status],
            color=["blue", "orange", "purple"]
        ),
        plt.title("Invoices by Status")
    ))

    # -------- CHART 3 – Payment Methods --------
    chart_methods = chart_image(lambda: (
        plt.bar(
            [p["payment_method"] for p in payments_by_method],
            [p["total"] for p in payments_by_method],
        ),
        plt.title("Payments by Method"),
        plt.xticks(rotation=45)
    ))

    # -------- CHART 4 – Total vs Paid vs Pending --------
    chart_total_bar = chart_image(lambda: (
        plt.bar(["Total", "Paid", "Pending"],
                [total_amount, total_paid, pending_amount],
                color=["black", "green", "red"]),
        plt.title("Amount Summary")
    ))

    # -------- CHART 5 – Paid Only --------
    chart_paid = chart_image(lambda: (
        plt.bar(["Paid"], [total_paid], color="green"),
        plt.title("Total Paid")
    ))

    # -------- CHART 6 – Pending Only --------
    chart_pending = chart_image(lambda: (
        plt.bar(["Pending"], [pending_amount], color="red"),
        plt.title("Total Pending")
    ))

    # --------------------- PDF -----------------------
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="Fees_Report.pdf"'
    c = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    # PAGE 1 – Summary
    c.setFont("Helvetica-Bold", 20)
    c.drawString(40, height - 40, "Fees Report")

    c.setFont("Helvetica", 12)
    c.drawString(40, height - 80, f"Total Amount: {total_amount}")
    c.drawString(40, height - 100, f"Paid: {total_paid}")
    c.drawString(40, height - 120, f"Pending: {pending_amount}")

    c.drawImage(chart_summary, 40, height - 450, width=400, height=350)
    c.showPage()

    # PAGE 2 – Invoice Status
    c.setFont("Helvetica-Bold", 18)
    c.drawString(40, height - 40, "Invoice Status")
    c.drawImage(chart_status, 40, height - 450, width=500, height=350)
    c.showPage()

    # PAGE 3 – Payment Methods
    c.setFont("Helvetica-Bold", 18)
    c.drawString(40, height - 40, "Payment Methods Summary")
    c.drawImage(chart_methods, 40, height - 450, width=500, height=350)
    c.showPage()

    # PAGE 4 – Total vs Paid vs Pending
    c.setFont("Helvetica-Bold", 18)
    c.drawString(40, height - 40, "Total vs Paid vs Pending Amount")
    c.drawImage(chart_total_bar, 40, height - 450, width=500, height=350)
    c.showPage()

    # PAGE 5 – Paid Only
    c.setFont("Helvetica-Bold", 18)
    c.drawString(40, height - 40, "Total Paid")
    c.drawImage(chart_paid, 150, height - 350, width=250, height=250)
    c.showPage()

    # PAGE 6 – Pending Only
    c.setFont("Helvetica-Bold", 18)
    c.drawString(40, height - 40, "Total Pending")
    c.drawImage(chart_pending, 150, height - 350, width=250, height=250)
    c.showPage()

    c.save()
    return response
