from django.urls import path
from . import views

app_name = 'sponsorship'

urlpatterns = [
    path('', views.sponsorship_page, name='sponsorship_page'),
    path('inquire/', views.submit_inquiry, name='submit_inquiry'),
    path('thank-you/', views.thank_you, name='thank_you'),
]
