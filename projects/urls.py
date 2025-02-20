from django.urls import path
from . import views

urlpatterns = [
    path('', views.project_list, name="project_list"),
    path('', views.create_project, name="create_project"),

    path('', views.login, name="login"),
    path('', views.signup, name="signup"),
]
