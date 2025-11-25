from django.urls import path
from . import views

urlpatterns = [
    path('', views.ReportDashboardView.as_view(), name='report_dashboard'),
    path('students/', views.student_report, name='student_report'),
    path('teachers/', views.teacher_report, name='teacher_report'),
    path('courses/', views.course_report, name='course_report'),
    path('attendance/', views.attendance_report, name='attendance_report'),
    path('fees/', views.fee_report, name='fee_report'),
]
