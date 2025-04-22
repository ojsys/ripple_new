from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.core.mail import send_mail, EmailMessage
from django.conf import settings
from .models import Pledge, Investment, CustomUser
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.urls import reverse

# Add this new signal handler for user registration
@receiver(post_save, sender=CustomUser)
def send_welcome_email_with_verification(sender, instance, created, **kwargs):
    try:
        if created:  # Only send when a new user is created
            # Generate verification token
            token = default_token_generator.make_token(instance)
            uid = urlsafe_base64_encode(force_bytes(instance.pk))
            
            # Create verification URL
            verify_url = f"{settings.SITE_URL}{reverse('verify_email', kwargs={'uidb64': uid, 'token': token})}"
            
            subject = "Welcome to Ripples - Please Verify Your Email"
            
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
                    
                    <p style="margin-top: 30px;">Best regards,<br>The Ripples Team</p>
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

@receiver(post_save, sender=Pledge)
def send_pledge_confirmation(sender, instance, created, **kwargs):
    try:
        if created:
            subject = f"Thank you for supporting {instance.project.title}!"
            
            html_message = f"""
            <!DOCTYPE html>
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px;">
                    <h2 style="color: #2c3e50; margin-bottom: 20px;">Thank You for Your Support! 🎉</h2>
                    
                    <p>Hello {instance.backer.get_full_name() or instance.backer.username},</p>
                    
                    <p>Thank you for your generous pledge to <strong style="color: #3498db;">{instance.project.title}</strong>. Your support means the world to this project and its creator!</p>
                    
                    <div style="background-color: #ffffff; padding: 15px; border-left: 4px solid #27ae60; margin: 20px 0;">
                        <p style="margin: 0;"><strong>Pledge Amount:</strong> ${instance.amount:,.2f}</p>
                        <p style="margin: 10px 0 0 0;"><strong>Project:</strong> {instance.project.title}</p>
                    </div>
                    
                    <p>You can track the project's progress and updates here:</p>
                    
                    <p style="text-align: center;">
                        <a href="{instance.project.get_absolute_url()}" style="display: inline-block; padding: 10px 20px; background-color: #27ae60; color: white; text-decoration: none; border-radius: 5px;">View Project</a>
                    </p>
                    
                    <p style="margin-top: 30px;">Best regards,<br>The Ripples Team</p>
                </div>
            </body>
            </html>
            """
            
            # Plain text version for email clients that don't support HTML
            text_message = f"""
            Hello {instance.backer.get_full_name() or instance.backer.username},
            
            Thank you for your generous pledge of ${instance.amount:,.2f} to {instance.project.title}. Your support means the world to this project and its creator!
            
            You can track the project's progress and updates here: {instance.project.get_absolute_url()}
            
            Best regards,
            The Ripples Team
            """
            
            email = EmailMessage(
                subject=subject,
                body=text_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[instance.backer.email],
                headers={'From': settings.DEFAULT_FROM_EMAIL}
            )
            email.content_subtype = 'html'  # Set the content type to HTML
            email.body = html_message
            email.send()
    except Exception as e:
        print(f"Email sending failed: {e}")

@receiver(post_save, sender=Investment)
def notify_founder_new_investment(sender, instance, created, **kwargs):
    try: 
        if created:
            subject = f"New Investment Proposal for {instance.project.title}"
            html_message = f"""
            <!DOCTYPE html>
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px;">
                    <h2 style="color: #2c3e50; margin-bottom: 20px;">New Investment Proposal! 🎉</h2>
                    
                    <p>Hello {instance.project.creator.username},</p>
                    
                    <p>Exciting news! Your project <strong style="color: #3498db;">{instance.project.title}</strong> has received a new investment proposal.</p>
                    
                    <div style="background-color: #ffffff; padding: 15px; border-left: 4px solid #3498db; margin: 20px 0;">
                        <p style="margin: 0;"><strong>Investment Amount:</strong> ${instance.amount:,.2f}</p>
                        <p style="margin: 10px 0 0 0;"><strong>Investor:</strong> {instance.investor.username}</p>
                    </div>
                    
                    <p>Please review this proposal at your earliest convenience:</p>
                    
                    <p style="text-align: center;">
                        <a href="{instance.project.get_absolute_url()}" style="display: inline-block; padding: 10px 20px; background-color: #3498db; color: white; text-decoration: none; border-radius: 5px;">Review Proposal</a>
                    </p>
                    
                    <p style="margin-top: 30px;">Best regards,<br>The Ripples Team</p>
                </div>
            </body>
            </html>
            """
            
            # Plain text version for email clients that don't support HTML
            text_message = f"""
            Hello {instance.project.creator.username},
            
            Exciting news! Your project {instance.project.title} has received a new investment proposal.
            
            Investment Amount: ${instance.amount:,.2f}
            Investor: {instance.investor.username}
            
            Review it here: {instance.project.get_absolute_url()}
            
            Best regards,
            The Ripples Team
            """
            
            # send_mail(
            #     subject,
            #     text_message,
            #     settings.DEFAULT_FROM_EMAIL,
            #     [instance.project.creator.email],
            #     html_message=html_message
            # )
            email = EmailMessage(
                subject=subject,
                body=text_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[instance.project.creator.email],
                headers={'From': settings.DEFAULT_FROM_EMAIL}
            )
            email.content_subtype = 'html'  # Set the content type to HTML
            email.body = html_message
            email.send()
    except Exception as e:
        print(f"Email sending failed: {e}")


@receiver(pre_delete, sender=Investment)
def update_project_on_investment_delete(sender, instance, **kwargs):
    try:
        if instance.status == 'active':  # Only reduce if the investment was active
            project = instance.project
            project.amount_raised -= instance.amount
            project.save()
    except Exception as e:
        print(f"Error updating project amount on investment deletion: {e}")
