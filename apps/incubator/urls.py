from django.urls import path
from . import views

app_name = 'incubator'

urlpatterns = [
    path('', views.incubator_page, name='incubator_page'),
    path('apply/', views.apply, name='apply'),
    path('thank-you/', views.thank_you, name='thank_you'),
]
