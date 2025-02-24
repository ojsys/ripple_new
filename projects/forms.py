from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Submit
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
        fields = ['amount']

    def __init__(self, *args, **kwargs):
        self.terms = kwargs.pop('terms', None)
        self.project = kwargs.pop('project', None)
        
        if not self.terms and not self.project:
            raise ValueError("InvestmentForm requires either 'terms' or 'project' argument.")
            
        super().__init__(*args, **kwargs)
        
        if self.terms:
            self.fields['amount'].widget.attrs['min'] = self.terms.minimum_investment
            self.fields['amount'].widget.attrs['max'] = self.terms.maximum_investment
        elif self.project:
            # For projects without terms, you might want to set some default constraints
            self.fields['amount'].widget.attrs['min'] = 1  # or any minimum you want
            self.fields['amount'].widget.attrs['max'] = self.project.funding_goal


    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        
        if self.terms:
            if amount < self.terms.minimum_investment:
                raise forms.ValidationError(f"Investment amount must be at least ${self.terms.minimum_investment}.")
        else:
            # For projects without terms, implement basic validation
            if amount <= 0:
                raise forms.ValidationError("Investment amount must be greater than zero.")
            if amount > self.project.funding_goal:
                raise forms.ValidationError(f"Investment amount cannot exceed the project funding goal of ${self.project.funding_goal}.")
        
        return amount


class PledgeForm(forms.ModelForm):
    class Meta:
        model = Pledge
        fields = ['amount', 'reward']

    def __init__(self, *args, **kwargs):
        # Extract project from kwargs before initializing parent
        self.project = kwargs.pop('project', None)
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Continue with Pledge', css_class='btn-success w-100'))
        
        # Filter rewards based on project
        if self.project:
            self.fields['reward'].queryset = self.project.rewards.all()

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