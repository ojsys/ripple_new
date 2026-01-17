from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Submit
from .models import (Project, Reward, InvestmentTerm, Investment,
                     Pledge, FundingType, IncubatorApplication)
from apps.accounts.models import CustomUser, FounderProfile, InvestorProfile, PartnerProfile
from ckeditor.widgets import CKEditorWidget
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth import get_user_model
from .signals import send_password_reset_email
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes








