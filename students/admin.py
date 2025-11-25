from django.contrib import admin
from .models import Student

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'get_full_name', 'gender', 'admission_date')
    list_filter = ('gender', 'admission_date')
    search_fields = ('student_id', 'user__first_name', 'user__last_name', 'parent_name')

    def get_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"

    get_full_name.short_description = 'Full Name'