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

# Remove the post_save signal for Pledge and create a function to be called after payment success
def send_pledge_confirmation_after_payment(pledge):
    try:
        subject = f"Thank you for supporting {pledge.project.title}!"
        
        html_message = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px;">
                <h2 style="color: #2c3e50; margin-bottom: 20px;">Thank You for Your Support! 🎉</h2>
                
                <p>Hello {pledge.backer.get_full_name() or pledge.backer.username},</p>
                
                <p>Thank you for your generous pledge to <strong style="color: #3498db;">{pledge.project.title}</strong>. Your support means the world to this project and its creator!</p>
                
                <div style="background-color: #ffffff; padding: 15px; border-left: 4px solid #27ae60; margin: 20px 0;">
                    <p style="margin: 0;"><strong>Pledge Amount:</strong> ${pledge.amount:,.2f}</p>
                    <p style="margin: 10px 0 0 0;"><strong>Project:</strong> {pledge.project.title}</p>
                </div>
                
                <p>You can track the project's progress and updates here:</p>
                
                <p style="text-align: center;">
                    <a href="{pledge.project.get_absolute_url()}" style="display: inline-block; padding: 10px 20px; background-color: #27ae60; color: white; text-decoration: none; border-radius: 5px;">View Project</a>
                </p>
                
                <p style="margin-top: 30px;">Best regards,<br>The StartUpRipples Team</p>
            </div>
        </body>
        </html>
        """
        
        # Plain text version for email clients that don't support HTML
        text_message = f"""
        Hello {pledge.backer.get_full_name() or pledge.backer.username},
        
        Thank you for your generous pledge of ${pledge.amount:,.2f} to {pledge.project.title}. Your support means the world to this project and its creator!
        
        You can track the project's progress and updates here: {pledge.project.get_absolute_url()}
        
        Best regards,
        The StartUpRipples Team
        """
        
        email = EmailMessage(
            subject=subject,
            body=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[pledge.backer.email],
            headers={'From': settings.DEFAULT_FROM_EMAIL}
        )
        email.content_subtype = 'html'  # Set the content type to HTML
        email.body = html_message
        email.send()
    except Exception as e:
        print(f"Pledge confirmation email sending failed: {e}")

# Remove the post_save signal for Investment and create a function to be called after payment success
def notify_founder_new_investment_after_payment(investment):
    try: 
        subject = f"New Investment Confirmed for {investment.project.title}"
        html_message = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px;">
                <h2 style="color: #2c3e50; margin-bottom: 20px;">New Investment Confirmed! 🎉</h2>
                
                <p>Hello {investment.project.creator.username},</p>
                
                <p>Great news! Your project <strong style="color: #3498db;">{investment.project.title}</strong> has received a new investment.</p>
                
                <div style="background-color: #ffffff; padding: 15px; border-left: 4px solid #3498db; margin: 20px 0;">
                    <p style="margin: 0;"><strong>Investment Amount:</strong> ${investment.amount:,.2f}</p>
                    <p style="margin: 10px 0 0 0;"><strong>Investor:</strong> {investment.investor.username}</p>
                    <p style="margin: 10px 0 0 0;"><strong>Equity Percentage:</strong> {investment.equity_percentage:.2f}%</p>
                </div>
                
                <p>You can view the details here:</p>
                
                <p style="text-align: center;">
                    <a href="{investment.project.get_absolute_url()}" style="display: inline-block; padding: 10px 20px; background-color: #3498db; color: white; text-decoration: none; border-radius: 5px;">View Project</a>
                </p>
                
                <p style="margin-top: 30px;">Best regards,<br>The StartUpRipples Team</p>
            </div>
        </body>
        </html>
        """
        
        # Plain text version for email clients that don't support HTML
        text_message = f"""
        Hello {investment.project.creator.username},
        
        Great news! Your project {investment.project.title} has received a new investment.
        
        Investment Amount: ${investment.amount:,.2f}
        Investor: {investment.investor.username}
        Equity Percentage: {investment.equity_percentage:.2f}%
        
        View it here: {investment.project.get_absolute_url()}
        
        Best regards,
        The STartUpRipples Team
        """
        
        email = EmailMessage(
            subject=subject,
            body=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[investment.project.creator.email],
            headers={'From': settings.DEFAULT_FROM_EMAIL}
        )
        email.content_subtype = 'html'  # Set the content type to HTML
        email.body = html_message
        email.send()
    except Exception as e:
        print(f"Investment confirmation email sending failed: {e}")

@receiver(pre_delete, sender=Investment)
def update_project_on_investment_delete(sender, instance, **kwargs):
    try:
        if instance.status == 'active':  # Only reduce if the investment was active
            project = instance.project
            project.amount_raised -= instance.amount
            project.save()
    except Exception as e:
        print(f"Error updating project amount on investment deletion: {e}")


def send_project_rejection_email(project):
    try:
        subject = f"Update on Your Project '{project.title}'"
        
        html_message = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px;">
                <h2 style="color: #2c3e50; margin-bottom: 20px;">Project Review Update</h2>
                
                <p>Hello {project.creator.get_full_name() or project.creator.username},</p>
                
                <p>We've reviewed your project <strong style="color: #e74c3c;">{project.title}</strong> and unfortunately, we are unable to approve it at this time.</p>
                
                <div style="background-color: #ffffff; padding: 15px; border-left: 4px solid #e74c3c; margin: 20px 0;">
                    <p style="margin: 0;"><strong>Reason for rejection:</strong></p>
                    <p style="margin: 10px 0 0 0;">{project.admin_notes or "No specific reason provided."}</p>
                </div>
                
                <p>You can make the necessary changes and resubmit your project for review. If you have any questions or need clarification, please don't hesitate to contact our support team.</p>
                
                <p style="margin-top: 30px;">Best regards,<br>The StartUpRipples Team</p>
            </div>
        </body>
        </html>
        """
        
        # Plain text version for email clients that don't support HTML
        text_message = f"""
        Hello {project.creator.get_full_name() or project.creator.username},
        
        We've reviewed your project '{project.title}' and unfortunately, we are unable to approve it at this time.
        
        Reason for rejection:
        {project.admin_notes or "No specific reason provided."}
        
        You can make the necessary changes and resubmit your project for review. If you have any questions or need clarification, please don't hesitate to contact our support team.
        
        Best regards,
        The StartUpRipples Team
        """
        
        email = EmailMessage(
            subject=subject,
            body=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[project.creator.email],
            headers={'From': settings.DEFAULT_FROM_EMAIL}
        )
        email.content_subtype = 'html'  # Set the content type to HTML
        email.body = html_message
        email.send()
    except Exception as e:
        print(f"Project rejection email sending failed: {e}")


def send_project_approval_email(project):
    try:
        subject = f"Your Project '{project.title}' Has Been Approved!"
        
        html_message = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px;">
                <h2 style="color: #2c3e50; margin-bottom: 20px;">Project Approved! 🎉</h2>
                
                <p>Hello {project.creator.get_full_name() or project.creator.username},</p>
                
                <p>We're excited to inform you that your project <strong style="color: #3498db;">{project.title}</strong> has been approved and is now live on our platform!</p>
                
                <div style="background-color: #ffffff; padding: 15px; border-left: 4px solid #27ae60; margin: 20px 0;">
                    <p style="margin: 0;"><strong>Project:</strong> {project.title}</p>
                    <p style="margin: 10px 0 0 0;"><strong>Funding Goal:</strong> ${project.funding_goal:,.2f}</p>
                    <p style="margin: 10px 0 0 0;"><strong>Deadline:</strong> {project.deadline.strftime('%B %d, %Y')}</p>
                </div>
                
                <p>You can view your project and share it with potential backers here:</p>
                
                <p style="text-align: center;">
                    <a href="{project.get_absolute_url()}" style="display: inline-block; padding: 10px 20px; background-color: #27ae60; color: white; text-decoration: none; border-radius: 5px;">View Your Project</a>
                </p>
                
                <p>Start promoting your project to your network to maximize your chances of success!</p>
                
                <p style="margin-top: 30px;">Best regards,<br>The StartUpRipples Team</p>
            </div>
        </body>
        </html>
        """
        
        # Plain text version for email clients that don't support HTML
        text_message = f"""
        Hello {project.creator.get_full_name() or project.creator.username},
        
        We're excited to inform you that your project '{project.title}' has been approved and is now live on our platform!
        
        Project: {project.title}
        Funding Goal: ${project.funding_goal:,.2f}
        Deadline: {project.deadline.strftime('%B %d, %Y')}
        
        You can view your project and share it with potential backers here: {project.get_absolute_url()}
        
        Start promoting your project to your network to maximize your chances of success!
        
        Best regards,
        The StartUpRipples Team
        """
        
        email = EmailMessage(
            subject=subject,
            body=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[project.creator.email],
            headers={'From': settings.DEFAULT_FROM_EMAIL}
        )
        email.content_subtype = 'html'  # Set the content type to HTML
        email.body = html_message
        email.send()
    except Exception as e:
        print(f"Project approval email sending failed: {e}")


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
