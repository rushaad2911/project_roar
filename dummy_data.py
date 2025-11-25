import random
import uuid
from datetime import date, timedelta, time
from django.core.management.base import BaseCommand
from faker import Faker

from accounts.models import User
from students.models import Student
from teachers.models import Teacher
from courses.models import Course, Schedule, Enrollment
from attendance.models import AttendanceRecord, StudentAttendance
from fees.models import FeeCategory, FeeInvoice, FeeInvoiceItem, Payment

fake = Faker()


class Command(BaseCommand):
    help = "Seed realistic dummy data for the Institute Management System"

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING("Deleting old data..."))
        self._clear_data()

        self.stdout.write(self.style.WARNING("Seeding data..."))
        self.create_users()
        self.create_teachers()
        self.create_students()
        self.create_courses()
        self.create_schedules()
        self.create_enrollments()
        self.create_attendance()
        self.create_fee_categories()
        self.create_fee_invoices_and_payments()

        self.stdout.write(self.style.SUCCESS("🎉 Dummy data created successfully!"))

    # ---------------- CLEAR OLD DATA ----------------
    def _clear_data(self):
        Payment.objects.all().delete()
        FeeInvoiceItem.objects.all().delete()
        FeeInvoice.objects.all().delete()
        FeeCategory.objects.all().delete()

        StudentAttendance.objects.all().delete()
        AttendanceRecord.objects.all().delete()
        Enrollment.objects.all().delete()
        Schedule.objects.all().delete()
        Course.objects.all().delete()

        Student.objects.all().delete()
        Teacher.objects.all().delete()
        User.objects.exclude(is_superuser=True).delete()

    # ---------------- USERS ----------------
    def create_users(self):
        # Admin user
        User.objects.create_superuser(
            username="admin",
            password="admin123",
            user_type="admin",
            email="admin@example.com",
        )

    # ---------------- TEACHERS ----------------
    def create_teachers(self):
        self.teachers = []
        for i in range(5):
            user = User.objects.create(
                username=f"teacher{i}",
                password="test1234",
                user_type="teacher",
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                mobile=fake.phone_number()
            )
            teacher = Teacher.objects.create(
                user=user,
                teacher_id=f"TCHR{i+1:03d}",
                gender=random.choice(["male", "female"]),
                qualification=random.choice(["M.Sc", "M.Tech", "PhD"]),
                experience=random.randint(1, 15),
            )
            self.teachers.append(teacher)

    # ---------------- STUDENTS ----------------
    def create_students(self):
        self.students = []
        for i in range(20):
            user = User.objects.create(
                username=f"student{i}",
                password="test1234",
                user_type="student",
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                mobile=fake.phone_number()
            )
            student = Student.objects.create(
                user=user,
                student_id=f"STD{i+1:03d}",
                gender=random.choice(["male", "female"]),
                parent_name=fake.name(),
                parent_mobile=fake.phone_number(),
            )
            self.students.append(student)

    # ---------------- COURSES ----------------
    def create_courses(self):
        course_names = [
            ("Mathematics I", "MATH101"),
            ("Physics I", "PHY101"),
            ("Computer Science Basics", "CS101"),
            ("Chemistry Basics", "CHEM101"),
            ("English Communication", "ENG101"),
        ]

        self.courses = []
        for name, code in course_names:
            course = Course.objects.create(
                name=name,
                code=code,
                description=fake.text(),
                credits=random.choice([3, 4]),
            )
            course.teachers.add(random.choice(self.teachers))
            self.courses.append(course)

    # ---------------- SCHEDULES ----------------
    def create_schedules(self):
        for course in self.courses:
            for day in ["monday", "wednesday", "friday"]:
                Schedule.objects.create(
                    course=course,
                    day=day,
                    start_time=time(9, 0),
                    end_time=time(10, 0),
                    room=f"Room {random.randint(100, 500)}",
                )

    # ---------------- ENROLLMENTS ----------------
    def create_enrollments(self):
        self.enrollments = []
        for student in self.students:
            enrolled_courses = random.sample(self.courses, k=3)
            for course in enrolled_courses:
                enrollment = Enrollment.objects.create(
                    student=student,
                    course=course,
                    status="active",
                )
                self.enrollments.append(enrollment)

    # ---------------- ATTENDANCE ----------------
    def create_attendance(self):
        for course in self.courses:
            for i in range(5):  # 5 days of attendance
                date_obj = date.today() - timedelta(days=i)
                record = AttendanceRecord.objects.create(course=course, date=date_obj)

                enrolled_students = Enrollment.objects.filter(course=course)
                for e in enrolled_students:
                    StudentAttendance.objects.create(
                        attendance_record=record,
                        student=e.student,
                        status=random.choice(["present", "absent", "late", "excused"])
                    )

    # ---------------- FEES ----------------
    def create_fee_categories(self):
        self.categories = [
            FeeCategory.objects.create(name="Tuition Fee", amount=50000),
            FeeCategory.objects.create(name="Library Fee", amount=2000),
            FeeCategory.objects.create(name="Lab Fee", amount=5000),
        ]

    def create_fee_invoices_and_payments(self):
        for student in self.students:
            invoice = FeeInvoice.objects.create(
                student=student,
                invoice_number=str(uuid.uuid4())[:8],
                total_amount=57000,
                paid_amount=0,
                due_date=date.today() + timedelta(days=30),
                status="pending",
            )

            # Items
            for cat in self.categories:
                FeeInvoiceItem.objects.create(
                    invoice=invoice,
                    category=cat,
                    amount=cat.amount,
                )

            # Payment
            if random.choice([True, False]):
                Payment.objects.create(
                    invoice=invoice,
                    amount=30000,
                    payment_method="cash",
                )
