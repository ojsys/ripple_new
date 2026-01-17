from django.db import models
from ckeditor.fields import RichTextField

class IncubatorAcceleratorPage(models.Model):
    title = models.CharField(max_length=200)
    program_description = RichTextField()
    image = models.ImageField(upload_to='accelerator/', blank=True)
    application_info = RichTextField(help_text="Information about the call for applications, eligibility, timeline, etc.")
    application_deadline = models.DateTimeField(null=True, blank=True)
    is_accepting_applications = models.BooleanField(default=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = "Incubator/Accelerator Page Content"



class IncubatorApplication(models.Model):
    # Applicant & Project Basics
    project = models.CharField(max_length=200, default='' )
    applicant_name = models.CharField(max_length=200, default='' )
    applicant_email = models.EmailField(default='' )
    applicant_phone = models.CharField(max_length=20, blank=True, default='' )
    applicant_company = models.CharField(max_length=200, blank=True, default='' )

    # Startup Fundamentals
    website = models.URLField(blank=True, default='www.website.com' )
    stage = models.CharField(
        max_length=50,
        choices=[
            ('idea', 'Idea Stage'),
            ('mvp', 'Minimum Viable Product'),
            ('launched', 'Launched'),
            ('growing', 'Growing/Scaling')
        ],
        default='idea'
    )
    industry = models.CharField(max_length=100, default='', help_text="e.g. FinTech, AgriTech, HealthTech")

    # Descriptions & Key Content
    application_text = RichTextField(blank=True, default='', help_text="Describe your startup and what problem it solves")
    traction = RichTextField(blank=True, default='', help_text="Mention any traction, pilot users, revenue, etc.")
    team_background = RichTextField(blank=True, default='', help_text="Tell us about your team and why you're the right people to build this")
    goals_for_program = models.TextField(blank=True, default='', help_text="What do you hope to achieve during the accelerator?")
    funding_raised = models.CharField(max_length=100, blank=True, default='', help_text="e.g. $10,000 in grants, $5,000 from friends & family")
    funding_needed = models.CharField(max_length=100, blank=True, default='', help_text="How much are you looking to raise post-program?")

    # File Uploads (Optional)
    pitch_deck = models.FileField(upload_to='pitch_decks/', default='', blank=True, help_text="Upload your pitch deck (PDF, max 10MB)")

    # Admin & Meta
    application_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
            ('waitlisted', 'Waitlisted')
        ],
        default='pending'
    )
    reviewed = models.BooleanField(default=False)

    def __str__(self):
        return f"Application for {self.project} by {self.applicant_name}"