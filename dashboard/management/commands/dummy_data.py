import random
import uuid
from datetime import date, timedelta, time
from django.core.management.base import BaseCommand
from faker import Faker
from django.db import connection

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
        self.fast_delete_all()

        self.stdout.write(self.style.WARNING("Seeding data..."))
        self.create_admin()
        self.create_teachers()
        self.create_students()
        self.create_courses()
        self.create_schedules()
        self.create_enrollments()
        self.create_attendance()
        self.create_fee_categories()
        self.create_fee_invoices_and_payments()

        self.stdout.write(self.style.SUCCESS("🎉 Dummy data created successfully!"))

    # ------------------------------------------------------------
    # FAST DELETE (Much faster than .delete())
    # ------------------------------------------------------------
    def fast_delete_all(self):
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys = OFF;")

        for table in connection.introspection.table_names():
            cursor.execute(f'DELETE FROM "{table}";')

        cursor.execute("PRAGMA foreign_keys = ON;")

    # ------------------------------------------------------------
    # CREATE ADMIN USER
    # ------------------------------------------------------------
    def create_admin(self):
        # Always recreate a fresh admin to avoid UNIQUE errors
        User.objects.filter(username="admin").delete()

        admin = User(
            username="admin",
            email="admin@example.com",
            user_type="admin",
        )
        admin.set_password("admin")
        admin.is_superuser = True
        admin.is_staff = True
        admin.save()

    # ------------------------------------------------------------
    # CREATE TEACHERS
    # ------------------------------------------------------------
    def create_teachers(self):
        self.teachers = []
        for i in range(5):
            user = User(
                username=f"teacher{i}",
                user_type="teacher",
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                mobile=fake.phone_number()
            )
            user.set_password("test1234")
            user.save()

            teacher = Teacher.objects.create(
                user=user,
                teacher_id=f"TCHR{i+1:03d}",
                gender=random.choice(["male", "female"]),
                qualification=random.choice(["M.Sc", "M.Tech", "PhD"]),
                experience=random.randint(1, 15),
            )
            self.teachers.append(teacher)

    # ------------------------------------------------------------
    # CREATE STUDENTS
    # ------------------------------------------------------------
    def create_students(self):
        self.students = []
        for i in range(20):
            user = User(
                username=f"student{i}",
                user_type="student",
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                mobile=fake.phone_number()
            )
            user.set_password("test1234")
            user.save()

            student = Student.objects.create(
                user=user,
                student_id=f"STD{i+1:03d}",
                gender=random.choice(["male", "female"]),
                parent_name=fake.name(),
                parent_mobile=fake.phone_number(),
            )
            self.students.append(student)

    # ------------------------------------------------------------
    # CREATE COURSES
    # ------------------------------------------------------------
    def create_courses(self):
        course_list = [
            ("Mathematics I", "MATH101"),
            ("Physics I", "PHY101"),
            ("Computer Science Basics", "CS101"),
            ("Chemistry Basics", "CHEM101"),
            ("English Communication", "ENG101"),
        ]

        self.courses = []
        for name, code in course_list:
            course = Course.objects.create(
                name=name,
                code=code,
                description=fake.text(),
                credits=random.choice([3, 4]),
            )
            course.teachers.add(random.choice(self.teachers))
            self.courses.append(course)

    # ------------------------------------------------------------
    # CREATE SCHEDULES
    # ------------------------------------------------------------
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

    # ------------------------------------------------------------
    # CREATE ENROLLMENTS
    # ------------------------------------------------------------
    def create_enrollments(self):
        self.enrollments = []
        for student in self.students:
            courses_to_enroll = random.sample(self.courses, k=3)
            for course in courses_to_enroll:
                enr = Enrollment.objects.create(
                    student=student,
                    course=course,
                    status="active",
                )
                self.enrollments.append(enr)

    # ------------------------------------------------------------
    # CREATE ATTENDANCE
    # ------------------------------------------------------------
    def create_attendance(self):
        for course in self.courses:
            for i in range(5):
                d = date.today() - timedelta(days=i)
                rec = AttendanceRecord.objects.create(
                    course=course,
                    date=d
                )

                enrolled_students = Enrollment.objects.filter(course=course)
                for e in enrolled_students:
                    StudentAttendance.objects.create(
                        attendance_record=rec,
                        student=e.student,
                        status=random.choice(["present", "absent", "late", "excused"])
                    )

    # ------------------------------------------------------------
    # FEE CATEGORIES
    # ------------------------------------------------------------
    def create_fee_categories(self):
        self.categories = [
            FeeCategory.objects.create(name="Tuition Fee", amount=50000),
            FeeCategory.objects.create(name="Library Fee", amount=2000),
            FeeCategory.objects.create(name="Lab Fee", amount=5000),
        ]

    # ------------------------------------------------------------
    # INVOICES + PAYMENTS
    # ------------------------------------------------------------
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

            # Add invoice items
            for cat in self.categories:
                FeeInvoiceItem.objects.create(
                    invoice=invoice,
                    category=cat,
                    amount=cat.amount
                )

            # Add payment randomly
            if random.choice([True, False]):
                Payment.objects.create(
                    invoice=invoice,
                    amount=30000,
                    payment_method="cash"
                )
