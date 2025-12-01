from django.urls import path
from . import views

urlpatterns = [
    path('', views.TeacherListView.as_view(), name='teacher_list'),
    path('<int:pk>/', views.TeacherDetailView.as_view(), name='teacher_detail'),
    path('create/', views.TeacherCreateView.as_view(), name='teacher_create'),
    path('<int:pk>/update/', views.TeacherUpdateView.as_view(), name='teacher_update'),
    path('<int:pk>/delete/', views.TeacherDeleteView.as_view(), name='teacher_delete'),
    
    path("publications/me/", views.PublicationListTeacherView.as_view(), name="publication_list_teacher"),

    path("<int:teacher_id>/publications/add/", views.PublicationCreateView.as_view(), name="publication_add"),
    path("publications/<int:pk>/edit/", views.PublicationUpdateView.as_view(), name="publication_edit"),
    path("publications/<int:pk>/delete/", views.PublicationDeleteView.as_view(), name="publication_delete"),
    path("publications/", views.PublicationListAdminView.as_view(), name="publication_list_admin"),

]
