from django.urls import path
from . import views

app_name = 'cms'

urlpatterns = [
    path('about/', views.about_page, name='about_page'),
    path('contact/', views.contact_page, name='contact_page'),
    path('contact/ajax/', views.contact_ajax, name='contact_ajax'),
    path('testimonials/', views.testimonials_page, name='testimonials'),
    path('team/', views.team_page, name='team'),

    # Legal Pages
    path('legal/<str:page_type>/', views.legal_page, name='legal_page'),
    path('terms-of-service/', views.terms_of_service, name='terms_of_service'),
    path('investor-terms/', views.investor_terms, name='investor_terms'),
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('cookie-policy/', views.cookie_policy, name='cookie_policy'),
]
