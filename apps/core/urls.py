from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('superadmin/', views.superadmin_dashboard, name='superadmin_dashboard'),
]
