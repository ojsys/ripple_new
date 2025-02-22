from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from .models import Pledge, Investment

@receiver(post_save, sender=Pledge)
def send_pledge_confirmation(sender, instance, created, **kwargs):
    if created:
        subject = f"Thank you for supporting {instance.project.title}!"
        message = f"""Hi {instance.backer.username},
        
        Thank you for your pledge of ${instance.amount} to {instance.project.title}.
        
        Project URL: {instance.project.get_absolute_url()}
        
        The Ripples Team"""
        send_mail(
            subject,
            message,
            'notifications@ripples.com',
            [instance.backer.email]
        )

@receiver(post_save, sender=Investment)
def notify_founder_new_investment(sender, instance, created, **kwargs):
    if created:
        subject = f"New Investment Proposal for {instance.project.title}"
        message = f"""Hi {instance.project.creator.username},
        
        You have a new investment proposal of ${instance.amount} from {instance.investor.username}.
        
        Review it here: {instance.project.get_absolute_url()}
        
        The Ripples Team"""
        send_mail(
            subject,
            message,
            'notifications@ripples.com',
            [instance.project.creator.email]
        )