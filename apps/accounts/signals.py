from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from apps.accounts.models import CustomUser
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.urls import reverse
from apps.core.email_templates import (
    get_base_email_template, get_warning_box, get_link_box,
    get_account_box, ICONS
)


@receiver(post_save, sender=CustomUser)
def send_welcome_email_with_verification(sender, instance, created, **kwargs):
    try:
        if created:  # Only send when a new user is created
            # Generate verification token
            token = default_token_generator.make_token(instance)
            uid = urlsafe_base64_encode(force_bytes(instance.pk))

            # Create verification URL
            verify_url = f"{getattr(settings, 'SITE_URL', 'https://startupripple.com')}{reverse('accounts:verify_email', kwargs={'uidb64': uid, 'token': token})}"

            subject = "Welcome to StartUpRipple - Please Verify Your Email"

            # Build email content
            user_name = instance.get_full_name() or instance.username

            content = f'''
            <p style="margin: 0 0 25px 0; font-size: 16px; line-height: 1.7; color: #4a5568; text-align: center;">
                Hi <strong style="color: #1a1a2e;">{user_name}</strong>,
            </p>

            <p style="margin: 0 0 25px 0; font-size: 16px; line-height: 1.7; color: #4a5568; text-align: center;">
                Welcome to StartUpRipple! We're thrilled to have you join our community of innovators and investors.
            </p>

            <p style="margin: 0 0 30px 0; font-size: 16px; line-height: 1.7; color: #4a5568; text-align: center;">
                To complete your registration and unlock all features, please verify your email address by clicking the button below.
            </p>
            '''

            content += get_warning_box(
                "<strong>Important:</strong> This verification link will expire in <strong>24 hours</strong> for security reasons."
            )

            content += '''
            <p style="margin: 25px 0 15px 0; font-size: 14px; line-height: 1.6; color: #718096; text-align: center;">
                If the button doesn't work, copy and paste this link into your browser:
            </p>
            '''
            content += get_link_box(verify_url)

            content += get_account_box("Your account email", instance.email)

            html_message = get_base_email_template(
                title="Welcome to StartUpRipple!",
                subtitle="Verify your email to get started",
                content=content,
                button_text="Verify My Email",
                button_url=verify_url,
                header_color="#26af59",
                icon=ICONS['wave'],
                footer_text="Didn't create this account? You can safely ignore this email."
            )

            # Plain text version
            text_message = f"""
Welcome to StartUpRipple!

Hi {user_name},

Thank you for joining StartUpRipple! We're excited to have you as part of our community of innovators and investors.

To complete your registration and verify your email address, please visit this link:
{verify_url}

This link will expire in 24 hours for security reasons.

If you didn't create this account, you can safely ignore this email.

Best regards,
The StartUpRipple Team
            """

            email = EmailMultiAlternatives(
                subject=subject,
                body=text_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[instance.email],
            )
            email.attach_alternative(html_message, "text/html")
            email.send()
    except Exception as e:
        print(f"Welcome email sending failed: {e}")


def send_password_reset_email(user, reset_url):
    """Send password reset email with beautiful template."""
    try:
        subject = "Reset Your StartUpRipple Password"
        user_name = user.get_full_name() or user.username

        content = f'''
        <p style="margin: 0 0 25px 0; font-size: 16px; line-height: 1.7; color: #4a5568; text-align: center;">
            Hi <strong style="color: #1a1a2e;">{user_name}</strong>,
        </p>

        <p style="margin: 0 0 30px 0; font-size: 16px; line-height: 1.7; color: #4a5568; text-align: center;">
            We received a request to reset the password for your StartUpRipple account. Click the button below to create a new password.
        </p>
        '''

        content += get_warning_box(
            "<strong>Important:</strong> This link will expire in <strong>24 hours</strong> for security reasons."
        )

        content += '''
        <p style="margin: 25px 0 15px 0; font-size: 14px; line-height: 1.6; color: #718096; text-align: center;">
            If the button doesn't work, copy and paste this link into your browser:
        </p>
        '''
        content += get_link_box(reset_url)

        content += get_account_box("Your account email", user.email)

        html_message = get_base_email_template(
            title="Password Reset Request",
            subtitle="Create a new password for your account",
            content=content,
            button_text="Reset My Password",
            button_url=reset_url,
            header_color="#26af59",
            icon=ICONS['lock'],
            footer_text="Didn't request this? You can safely ignore this email."
        )

        text_message = f"""
Reset Your StartUpRipple Password

Hi {user_name},

We received a request to reset your password for your StartUpRipple account. If you didn't make this request, you can safely ignore this email.

To reset your password, please visit this link:
{reset_url}

This link will expire in 24 hours for security reasons.

Best regards,
The StartUpRipple Team
        """

        email = EmailMultiAlternatives(
            subject=subject,
            body=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        email.attach_alternative(html_message, "text/html")
        email.send()
    except Exception as e:
        print(f"Password reset email sending failed: {e}")
