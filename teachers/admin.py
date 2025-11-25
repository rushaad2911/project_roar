from django.contrib import admin
from .models import Teacher

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('teacher_id', 'get_full_name', 'qualification', 'experience', 'date_joined')
    list_filter = ('gender', 'date_joined')
    search_fields = ('teacher_id', 'user__first_name', 'user__last_name', 'qualification')

    def get_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"

    get_full_name.short_description = 'Full Name'