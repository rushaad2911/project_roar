# resume_analyzer/urls.py
from django.urls import path
from . import views

app_name = "resume_analyzer"

urlpatterns = [
    path("", views.index, name="index"),
    path("analyze/", views.analyze, name="analyze"),
]
