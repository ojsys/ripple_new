from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field
from .models import (Project, Reward, InvestmentTerm, Investment, 
                     Pledge, FundingType, CustomUser, FounderProfile, InvestorProfile)


class SignUpForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'user_type']

    def clean_password2(self):
        cd = self.cleaned_data
        if cd['password'] != cd['password2']:
            raise forms.ValidationError('Passwords don\'t match.')
        return cd['password2']



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


class BaseProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'phone_number']

class FounderProfileForm(forms.ModelForm):
    class Meta:
        model = FounderProfile
        fields = ['company_name', 'website', 'bio', 'image']
        widgets = {
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

class InvestorProfileForm(forms.ModelForm):
    class Meta:
        model = InvestorProfile
        fields = ['investment_focus', 'preferred_industries']
        widgets = {
            'investment_focus': forms.Textarea(attrs={'rows': 3}),
            'preferred_industries': forms.TextInput(attrs={
                'placeholder': 'e.g., Technology, Agriculture, Healthcare'
            }),
        }

class EditProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'user_type']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'user_type': forms.Select(attrs={'class': 'form-control'}),
        }