from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import EmailMessage
from django.conf import settings
from apps.accounts.models import CustomUser
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.urls import reverse

@receiver(post_save, sender=CustomUser)
def send_welcome_email_with_verification(sender, instance, created, **kwargs):
    try:
        if created:  # Only send when a new user is created
            # Generate verification token
            token = default_token_generator.make_token(instance)
            uid = urlsafe_base64_encode(force_bytes(instance.pk))
            
            # Create verification URL
            verify_url = f"{settings.SITE_URL}{reverse('accounts:verify_email', kwargs={'uidb64': uid, 'token': token})}"
            
            subject = "Welcome to StartUpRipples - Please Verify Your Email"
            
            html_message = f"""
            <!DOCTYPE html>
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px;">
                    <h2 style="color: #2c3e50; margin-bottom: 20px;">Welcome to Ripples! 🌊</h2>
                    
                    <p>Hello {instance.get_full_name() or instance.username},</p>
                    
                    <p>Thank you for joining Ripples! We're excited to have you as part of our community of innovators and investors.</p>
                    
                    <p>To complete your registration and verify your email address, please click the button below:</p>
                    
                    <p style="text-align: center;">
                        <a href="{verify_url}" style="display: inline-block; padding: 10px 20px; background-color: #27ae60; color: white; text-decoration: none; border-radius: 5px;">Verify Email Address</a>
                    </p>
                    
                    <p>If the button doesn't work, you can copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; background-color: #f1f1f1; padding: 10px; border-radius: 3px;">{verify_url}</p>
                    
                    <p>This link will expire in 24 hours for security reasons.</p>
                    
                    <p style="margin-top: 30px;">Best regards,<br>The StartUpRipples Team</p>
                </div>
            </body>
            </html>
            """
            
            # Plain text version for email clients that don't support HTML
            text_message = f"""
            Hello {instance.get_full_name() or instance.username},
            
            Thank you for joining Ripples! We're excited to have you as part of our community of innovators and investors.
            
            To complete your registration and verify your email address, please visit this link:
            {verify_url}
            
            This link will expire in 24 hours for security reasons.
            
            Best regards,
            The Ripples Team
            """
            
            email = EmailMessage(
                subject=subject,
                body=text_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[instance.email],
                headers={'From': settings.DEFAULT_FROM_EMAIL}
            )
            email.content_subtype = 'html'  # Set the content type to HTML
            email.body = html_message
            email.send()
    except Exception as e:
        print(f"Welcome email sending failed: {e}")


def send_password_reset_email(user, reset_url):
    try:
        subject = "Reset Your StartUpRipples Password"
        
        html_message = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px;">
                <h2 style="color: #2c3e50; margin-bottom: 20px;">Reset Your Password</h2>
                
                <p>Hello {user.get_full_name() or user.username},</p>
                
                <p>We received a request to reset your password for your StartUpRipples account. If you didn't make this request, you can safely ignore this email.</p>
                
                <p>To reset your password, please click the button below:</p>
                
                <p style="text-align: center;">
                    <a href="{reset_url}" style="display: inline-block; padding: 10px 20px; background-color: #27ae60; color: white; text-decoration: none; border-radius: 5px;">Reset Password</a>
                </p>
                
                <p>If the button doesn't work, you can copy and paste this link into your browser:</p>
                <p style="word-break: break-all; background-color: #f1f1f1; padding: 10px; border-radius: 3px;">{reset_url}</p>
                
                <p>This link will expire in 24 hours for security reasons.</p>
                
                <p style="margin-top: 30px;">Best regards,<br>The StartUpRipples Team</p>
            </div>
        </body>
        </html>
        """
        
        # Plain text version for email clients that don't support HTML
        text_message = f"""
        Hello {user.get_full_name() or user.username},
        
        We received a request to reset your password for your StartUpRipples account. If you didn't make this request, you can safely ignore this email.
        
        To reset your password, please visit this link:
        {reset_url}
        
        This link will expire in 24 hours for security reasons.
        
        Best regards,
        The StartUpRipples Team
        """
        
        email = EmailMessage(
            subject=subject,
            body=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
            headers={'From': settings.DEFAULT_FROM_EMAIL}
        )
        email.content_subtype = 'html'  # Set the content type to HTML
        email.body = html_message
        email.send()
    except Exception as e:
        print(f"Password reset email sending failed: {e}")