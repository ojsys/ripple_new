import logging
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings

logger = logging.getLogger(__name__)

# Track status before save so we can detect the transition
_previous_status = {}


@receiver(pre_save, sender='incubator.IncubatorApplication')
def capture_previous_status(sender, instance, **kwargs):
    if instance.pk:
        try:
            _previous_status[instance.pk] = sender.objects.get(pk=instance.pk).status
        except sender.DoesNotExist:
            pass


@receiver(post_save, sender='incubator.IncubatorApplication')
def provision_lms_on_approval(sender, instance, created, **kwargs):
    old_status = _previous_status.pop(instance.pk, None)

    # Only fire when transitioning TO 'approved' and not already provisioned
    if instance.status != 'approved':
        return
    if instance.lms_provisioned:
        return
    if old_status == 'approved':
        # Already was approved (re-save without status change)
        return

    _provision_student_account(instance)


def _provision_student_account(application):
    User = get_user_model()

    # ── 1. Build name parts from applicant_name ────────────────────────────
    parts = application.applicant_name.strip().split()
    first_name = parts[0] if parts else ''
    last_name = ' '.join(parts[1:]) if len(parts) > 1 else ''

    # ── 2. Create or get user ──────────────────────────────────────────────
    password = None
    user_created = False

    user = User.objects.filter(email=application.applicant_email).first()
    if user is None:
        password = get_random_string(
            12, 'abcdefghijkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789'
        )
        base_username = application.applicant_email.split('@')[0]
        username = base_username
        suffix = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{suffix}"
            suffix += 1

        user = User.objects.create_user(
            username=username,
            email=application.applicant_email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            user_type='founder',
            email_verified=True,
            is_active=True,
        )
        user_created = True
        logger.info("Created student account for %s", application.applicant_email)
    else:
        # Existing user — ensure they're a founder type
        if not user.user_type:
            user.user_type = 'founder'
            user.save(update_fields=['user_type'])

    # ── 3. Enroll in LMS ───────────────────────────────────────────────────
    try:
        from apps.lms.models import LMSCourse, LMSEnrollment
        course = LMSCourse.objects.filter(is_active=True).first()
        if course:
            LMSEnrollment.objects.get_or_create(user=user, course=course)
            logger.info("Enrolled %s in LMS course: %s", user.email, course.title)
    except Exception as exc:
        logger.error("LMS enrollment failed for %s: %s", user.email, exc)

    # ── 4. Send congratulations email ──────────────────────────────────────
    try:
        site_url = getattr(settings, 'SITE_URL', 'https://startupripple.com')
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'LaunchPadi <noreply@startupripple.com>')

        dashboard_path = '/lms/dashboard/'
        context = {
            'first_name': first_name or application.applicant_name,
            'email': application.applicant_email,
            'password': password,
            'user_created': user_created,
            'login_url': f"{site_url}/accounts/login/",
            # Link directly to login with ?next= so the user lands on the dashboard
            # after a single login step, regardless of whether they're already logged in.
            'dashboard_url': f"{site_url}/accounts/login/?next={dashboard_path}",
            'lms_url': f"{site_url}/lms/",
            'site_url': site_url,
        }

        subject = "🎉 Congratulations — You're in! Your LaunchPadi account is ready"
        html_body = render_to_string('incubator/emails/approval_email.html', context)
        text_body = render_to_string('incubator/emails/approval_email.txt', context)

        msg = EmailMultiAlternatives(subject, text_body, from_email, [application.applicant_email])
        msg.attach_alternative(html_body, 'text/html')
        msg.send()
        logger.info("Approval email sent to %s", application.applicant_email)
    except Exception as exc:
        logger.error("Failed to send approval email to %s: %s", application.applicant_email, exc)

    # ── 5. Mark as provisioned ─────────────────────────────────────────────
    # Use update() to avoid triggering the signal again
    sender_model = application.__class__
    sender_model.objects.filter(pk=application.pk).update(lms_provisioned=True)
