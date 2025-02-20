from django import forms
from .models import Project, Reward, InvestmentTerm, Investment, Pledge, FundingType

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = [
            'title', 'description', 'funding_type', 'category', 
            'funding_goal', 'deadline', 'image'
        ]
        widgets = {
            'deadline': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

class RewardForm(forms.ModelForm):
    class Meta:
        model = Reward
        fields = ['title', 'description', 'amount']

class InvestmentTermForm(forms.ModelForm):
    class Meta:
        model = InvestmentTerm
        fields = ['equity_offered', 'minimum_investment', 'valuation', 'deadline']
        widgets = {
            'deadline': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

class InvestmentForm(forms.ModelForm):
    class Meta:
        model = Investment
        fields = ['amount', 'terms']

    def __init__(self, *args, **kwargs):
        terms = kwargs.pop('terms', None)
        super().__init__(*args, **kwargs)
        if terms:
            self.fields['terms'].queryset = terms

class PledgeForm(forms.ModelForm):
    class Meta:
        model = Pledge
        fields = ['amount', 'reward']

    def __init__(self, *args, **kwargs):
        project = kwargs.pop('project', None)
        super().__init__(*args, **kwargs)
        if project:
            self.fields['reward'].queryset = Reward.objects.filter(project=project)