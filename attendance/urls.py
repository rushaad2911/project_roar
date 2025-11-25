from django.urls import path
from . import views

urlpatterns = [
    path('', views.AttendanceRecordListView.as_view(), name='attendance_record_list'),
    path('<int:pk>/', views.AttendanceRecordDetailView.as_view(), name='attendance_record_detail'),
    path('create/', views.AttendanceRecordCreateView.as_view(), name='attendance_record_create'),
    path('<int:pk>/update/', views.update_attendance, name='update_attendance'),
    path('<int:pk>/delete/', views.AttendanceRecordDeleteView.as_view(), name='attendance_record_delete'),
    path('report/', views.StudentAttendanceReportView.as_view(), name='student_attendance_report'),
]
