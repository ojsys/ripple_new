from django.urls import path
from . import views

app_name = 'lms'

urlpatterns = [
    path('', views.lms_home, name='lms_home'),
    path('enroll/', views.lms_enroll, name='lms_enroll'),
    path('dashboard/', views.lms_dashboard, name='lms_dashboard'),
    path('module/<int:pk>/', views.module_detail, name='module_detail'),
    path('lesson/<int:pk>/', views.lesson_detail, name='lesson_detail'),
    path('deliverable/<int:pk>/submit/', views.submit_deliverable, name='submit_deliverable'),
]
