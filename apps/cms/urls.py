from django.urls import path
from . import views

app_name = 'cms'

urlpatterns = [
    path('about/', views.about_page, name='about_page'),
    path('contact/', views.contact_page, name='contact_page'),
    path('contact/ajax/', views.contact_ajax, name='contact_ajax'),
    path('testimonials/', views.testimonials_page, name='testimonials'),
    path('team/', views.team_page, name='team'),
]
