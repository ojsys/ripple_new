from django.shortcuts import render
from .models import Project


def project_list(request):
    projects = Project.objects.all()
    return render(request, 'projects/project_list.html', {'projects': projects})


def create_project(request):
    pass




def login(request):
    pass




def signup(request):
    pass
