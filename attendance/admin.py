from django.contrib import admin
from .models import AttendanceRecord, StudentAttendance

class StudentAttendanceInline(admin.TabularInline):
    model = StudentAttendance
    extra = 1

@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ('course', 'date', 'created_at')
    list_filter = ('date', 'course')
    search_fields = ('course__name', 'course__code')
    inlines = [StudentAttendanceInline]

@admin.register(StudentAttendance)
class StudentAttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'get_date', 'status', 'get_course')
    list_filter = ('status', 'attendance_record__date', 'attendance_record__course')
    search_fields = ('student__user__first_name', 'student__user__last_name', 'remarks')

    def get_date(self, obj):
        return obj.attendance_record.date
    get_date.short_description = 'Date'
    get_date.admin_order_field = 'attendance_record__date'

    def get_course(self, obj):
        return obj.attendance_record.course
    get_course.short_description = 'Course'
    get_course.admin_order_field = 'attendance_record__course'