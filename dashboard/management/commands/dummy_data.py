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
from department.models import Department

fake = Faker()


class Command(BaseCommand):
    help = "Seed FAST dummy data for the Institute Management System"

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING("Deleting old data..."))
        self.fast_delete_all()

        self.stdout.write(self.style.WARNING("Seeding data..."))

        self.load_departments()
        self.create_admin()
        self.create_teachers()
        self.create_students()
        self.create_courses()
        self.create_schedules()
        self.create_enrollments()
        self.create_attendance()
        self.create_fee_categories()
        self.create_fee_invoices_and_payments()

        self.stdout.write(self.style.SUCCESS("🎉 FAST Dummy data created successfully!"))

    # ------------------------------------------------------------
    # FAST DELETE
    # ------------------------------------------------------------
    def fast_delete_all(self):
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys = OFF;")

        for table in connection.introspection.table_names():
            cursor.execute(f'DELETE FROM "{table}";')

        cursor.execute("PRAGMA foreign_keys = ON;")

    # ------------------------------------------------------------
    # LOAD / CREATE DEPARTMENTS
    # ------------------------------------------------------------
    def load_departments(self):
        required = ["Civil", "IT", "Mechanical", "Electronics", "Computer Science"]

        for name in required:
            Department.objects.get_or_create(name=name)

        self.departments = list(Department.objects.all())
        print(f"Loaded departments: {[d.name for d in self.departments]}")

    # ------------------------------------------------------------
    # ADMIN
    # ------------------------------------------------------------
    def create_admin(self):
        User.objects.filter(username="admin").delete()
        admin = User(
            username="admin",
            email="admin@example.com",
            user_type="admin",
            department=None,
        )
        admin.set_password("admin")
        admin.is_superuser = True
        admin.is_staff = True
        admin.save()

    # ------------------------------------------------------------
    # FAST TEACHER CREATION
    # ------------------------------------------------------------
    def create_teachers(self):
        teacher_users = []

        # create teacher user objects
        for dept in self.departments:
            for i in range(5):
                user = User(
                    username=f"teacher_{dept.name[:3]}_{i}",
                    user_type="teacher",
                    department=dept,
                    first_name=fake.first_name(),
                    last_name=fake.last_name(),
                    mobile=fake.phone_number(),
                )
                user.set_password("test1234")
                teacher_users.append(user)

        # bulk insert users
        User.objects.bulk_create(teacher_users)

        # fetch saved users
        created_user_list = list(User.objects.filter(user_type="teacher"))
        teacher_objs = []

        idx = 0
        for dept in self.departments:
            for i in range(5):
                teacher_objs.append(
                    Teacher(
                        user=created_user_list[idx],
                        teacher_id=f"TCHR_{dept.id}_{i+1:03d}",
                        gender=random.choice(["male", "female"]),
                        qualification=random.choice(["M.Sc", "M.Tech", "PhD"]),
                        experience=random.randint(1, 15),
                    )
                )
                idx += 1

        Teacher.objects.bulk_create(teacher_objs)
        self.teachers = list(Teacher.objects.all())

    # ------------------------------------------------------------
    # FAST STUDENT CREATION
    # ------------------------------------------------------------
    def create_students(self):
        student_users = []

        for dept in self.departments:
            for i in range(60):
                user = User(
                    username=f"student_{dept.name[:3]}_{i}",
                    user_type="student",
                    department=dept,
                    first_name=fake.first_name(),
                    last_name=fake.last_name(),
                    mobile=fake.phone_number(),
                )
                user.set_password("test1234")
                student_users.append(user)

        User.objects.bulk_create(student_users)

        created_students_users = list(User.objects.filter(user_type="student"))
        student_objs = []

        for idx, user in enumerate(created_students_users):
            dept = user.department
            local_id = idx % 60
            student_objs.append(
                Student(
                    user=user,
                    student_id=f"STD_{dept.id}_{local_id+1:03d}",
                    gender=random.choice(["male", "female"]),
                    parent_name=fake.name(),
                    parent_mobile=fake.phone_number(),
                )
            )

        Student.objects.bulk_create(student_objs)
        self.students = list(Student.objects.all())

    # ------------------------------------------------------------
    # COURSES
    # ------------------------------------------------------------
    def create_courses(self):
        course_list = [
            ("Mathematics I", "MATH101"),
            ("Physics I", "PHY101"),
            ("Computer Science Basics", "CS101"),
            ("Chemistry Basics", "CHEM101"),
            ("English Communication", "ENG101"),
        ]

        courses_to_create = []

        for name, code in course_list:
            courses_to_create.append(
                Course(
                    name=name,
                    code=code,
                    description=fake.text(),
                    credits=random.choice([3, 4]),
                )
            )

        Course.objects.bulk_create(courses_to_create)
        self.courses = list(Course.objects.all())

        # attach teacher (random)
        for course in self.courses:
            course.teachers.add(random.choice(self.teachers))

    # ------------------------------------------------------------
    # SCHEDULES
    # ------------------------------------------------------------
    def create_schedules(self):
        schedules = []
        for course in self.courses:
            for day in ["monday", "wednesday", "friday"]:
                schedules.append(
                    Schedule(
                        course=course,
                        day=day,
                        start_time=time(9, 0),
                        end_time=time(10, 0),
                        room=f"Room {random.randint(100, 500)}",
                    )
                )
        Schedule.objects.bulk_create(schedules)

    # ------------------------------------------------------------
    # FAST ENROLLMENTS
    # ------------------------------------------------------------
    def create_enrollments(self):
        enrollments = []

        for student in self.students:
            selected = random.sample(self.courses, 3)
            for course in selected:
                enrollments.append(
                    Enrollment(
                        student=student,
                        course=course,
                        status="active",
                    )
                )

        Enrollment.objects.bulk_create(enrollments)
        self.enrollments = list(Enrollment.objects.all())

    # ------------------------------------------------------------
    # FAST ATTENDANCE CREATION
    # ------------------------------------------------------------
    def create_attendance(self):
        attendance_records = []
        student_attendance_rows = []

        # create attendance rows for each course for last 5 days
        for course in self.courses:
            for i in range(5):
                d = date.today() - timedelta(days=i)
                attendance_records.append(
                    AttendanceRecord(course=course, date=d)
                )

        AttendanceRecord.objects.bulk_create(attendance_records)
        attendance_records = list(AttendanceRecord.objects.all())

        # create student attendance in large batches
        for rec in attendance_records:
            enrolled = [enr.student for enr in self.enrollments if enr.course_id == rec.course_id]
            for student in enrolled:
                student_attendance_rows.append(
                    StudentAttendance(
                        attendance_record=rec,
                        student=student,
                        status=random.choice(["present", "absent", "late", "excused"]),
                    )
                )

        StudentAttendance.objects.bulk_create(student_attendance_rows)

    # ------------------------------------------------------------
    # FEES
    # ------------------------------------------------------------
    def create_fee_categories(self):
        self.categories = [
            FeeCategory.objects.create(name="Tuition Fee", amount=50000),
            FeeCategory.objects.create(name="Library Fee", amount=2000),
            FeeCategory.objects.create(name="Lab Fee", amount=5000),
        ]

    def create_fee_invoices_and_payments(self):
        invoices = []
        items = []
        payments = []

        for student in self.students:
            invoice = FeeInvoice(
                student=student,
                invoice_number=str(uuid.uuid4())[:8],
                total_amount=57000,
                paid_amount=0,
                due_date=date.today() + timedelta(days=30),
                status="pending",
            )
            invoices.append(invoice)

        FeeInvoice.objects.bulk_create(invoices)
        invoices = list(FeeInvoice.objects.all())

        for invoice in invoices:
            for cat in self.categories:
                items.append(
                    FeeInvoiceItem(
                        invoice=invoice,
                        category=cat,
                        amount=cat.amount,
                    )
                )
            if random.choice([True, False]):
                payments.append(
                    Payment(
                        invoice=invoice,
                        amount=30000,
                        payment_method="cash",
                    )
                )

        FeeInvoiceItem.objects.bulk_create(items)
        Payment.objects.bulk_create(payments)
