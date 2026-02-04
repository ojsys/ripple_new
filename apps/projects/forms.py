from django import forms
from django.forms import inlineformset_factory
from ckeditor.widgets import CKEditorWidget
from .models import Project, Reward, Update, Donation
from apps.funding.models import Investment, InvestmentTerm


class ProjectForm(forms.ModelForm):
    """Form for creating and editing projects."""

    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 10,
            'id': 'description-editor'
        }),
        required=True
    )

    class Meta:
        model = Project
        fields = [
            'title', 'short_description', 'description', 'category', 'funding_type',
            'funding_goal', 'deadline', 'image', 'location', 'video_url'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Give your project a compelling title'
            }),
            'short_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Write a brief summary that captures your project essence (max 255 characters)',
                'maxlength': '255'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'funding_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'funding_goal': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '10000'
            }),
            'deadline': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Lagos, Nigeria'
            }),
            'video_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://youtube.com/watch?v=...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].empty_label = "Select Category"
        self.fields['funding_type'].empty_label = "Select Funding Type"


class RewardForm(forms.ModelForm):
    """Form for creating and editing project rewards."""

    class Meta:
        model = Reward
        fields = ['title', 'description', 'amount']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Reward title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe what backers will receive...'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Minimum pledge amount',
                'min': '1'
            }),
        }


# Formset for managing multiple rewards during project creation/editing
RewardFormSet = inlineformset_factory(
    Project,
    Reward,
    form=RewardForm,
    extra=3,  # Show 3 empty reward forms by default
    can_delete=True,
    min_num=0,
    validate_min=False,
)


class UpdateForm(forms.ModelForm):
    """Form for posting project updates."""

    class Meta:
        model = Update
        fields = ['title', 'content']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Update title'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Share your progress with backers...'
            }),
        }


class DonationForm(forms.ModelForm):
    """Form for making donations to projects."""

    class Meta:
        model = Donation
        fields = ['amount', 'reward', 'message', 'is_anonymous']
        widgets = {
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter amount in USD',
                'min': '1'
            }),
            'reward': forms.Select(attrs={
                'class': 'form-select'
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Leave a message for the creator (optional)'
            }),
            'is_anonymous': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def __init__(self, *args, project=None, **kwargs):
        super().__init__(*args, **kwargs)
        if project:
            self.fields['reward'].queryset = project.rewards.all()
            self.fields['reward'].required = False
        self.fields['reward'].empty_label = "Select a Reward (Optional)"


class InvestmentForm(forms.ModelForm):
    """Form for submitting investments."""

    class Meta:
        model = Investment
        fields = ['amount', 'terms']
        widgets = {
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Investment amount in USD'
            }),
            'terms': forms.Select(attrs={
                'class': 'form-select'
            }),
        }

    def __init__(self, *args, project=None, **kwargs):
        super().__init__(*args, **kwargs)
        if project:
            self.fields['terms'].queryset = project.investment_terms.all()
            self.fields['terms'].required = False
        self.fields['terms'].empty_label = "Select Investment Terms"
