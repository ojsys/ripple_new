from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from django.urls import reverse
from django.conf import settings
from django.db import transaction
from django.db.models import F, ExpressionWrapper, FloatField
from ckeditor.fields import RichTextField
