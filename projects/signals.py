from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.core.mail import send_mail, EmailMessage
from django.conf import settings
from .models import Pledge, Investment

@receiver(post_save, sender=Pledge)
def send_pledge_confirmation(sender, instance, created, **kwargs):
    try:
        if created:
            subject = f"Thank you for supporting {instance.project.title}!"
            message = f"""Hi {instance.backer.username},
            
            Thank you for your pledge of ${instance.amount} to {instance.project.title}.
            
            Project URL: {instance.project.get_absolute_url()}
            
            The Ripples Team"""
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [instance.backer.email]
            )
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
