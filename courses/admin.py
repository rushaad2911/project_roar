from django.contrib import admin
from .models import Course, Enrollment, Schedule

class ScheduleInline(admin.TabularInline):
    model = Schedule
    extra = 1

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'credits', 'created_at')
    list_filter = ('credits', 'created_at')
    search_fields = ('code', 'name', 'description')
    filter_horizontal = ('teachers',)
    inlines = [ScheduleInline]

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'status', 'enrollment_date', 'grade')
    list_filter = ('status', 'enrollment_date')
    search_fields = ('student__user__first_name', 'student__user__last_name', 'course__name')

@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('course', 'day', 'start_time', 'end_time', 'room')
    list_filter = ('day',)
    search_fields = ('course__name', 'room')