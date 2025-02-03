from django.contrib import admin
from .models import Category, Project, Reward, Pledge, Update

admin.site.register(Category)
admin.site.register(Project)
admin.site.register(Reward)
admin.site.register(Pledge)
admin.site.register(Update)