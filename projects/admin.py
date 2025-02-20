from django.contrib import admin
from .models import (
    Category, Project, FundingType, 
    Reward, Pledge, InvestmentTerm, Investment
)

admin.site.register(Category)
admin.site.register(FundingType)
admin.site.register(Project)
admin.site.register(Reward)
admin.site.register(Pledge)
admin.site.register(InvestmentTerm)
admin.site.register(Investment)