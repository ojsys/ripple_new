from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('superadmin/', views.analytics_dashboard, name='analytics_dashboard'),
]
