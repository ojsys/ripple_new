from django.db import models
from ckeditor.fields import RichTextField


class IncubatorAcceleratorPage(models.Model):
    # ── Hero ──────────────────────────────────────────────────────────────────
    hero_title = models.CharField(
        max_length=300,
        default="Build Your Idea Into a Business — With the Right Support",
    )
    hero_subtitle = models.TextField(
        default=(
            "A cohort-based accelerator for Nigerian founders at the idea and early-MVP stage. "
            "Curriculum. Mentorship. Community. A real chance at funding."
        ),
    )

    # ── Stats bar (hero) ──────────────────────────────────────────────────────
    stat_weeks = models.CharField(max_length=20, default="12")
    stat_lessons = models.CharField(max_length=20, default="48+")
    stat_mentorship = models.CharField(max_length=40, default="1:1")
    stat_event = models.CharField(max_length=60, default="Demo Day")
    stat_cost = models.CharField(max_length=40, default="Free")

    # ── Pillars section ───────────────────────────────────────────────────────
    pillars_section_title = models.CharField(
        max_length=200,
        default="Four pillars. One transformative program.",
    )
    pillars_section_subtitle = models.TextField(
        default=(
            "LaunchPadi isn't just a course — it's a complete founder development experience "
            "built for the Nigerian ecosystem."
        ),
    )

    # ── Curriculum section ────────────────────────────────────────────────────
    curriculum_section_title = models.CharField(
        max_length=200,
        default="One module per week. Built for idea-stage founders.",
    )
    curriculum_section_subtitle = models.TextField(
        default=(
            "Each week covers a new building block of your startup — with lessons, "
            "a practical exercise, and a deliverable you keep after the program."
        ),
    )

    # ── Who should apply ──────────────────────────────────────────────────────
    who_section_title = models.CharField(max_length=200, default="You're the right fit if…")
    who_section_intro = models.TextField(
        default=(
            "LaunchPadi is highly selective. We look for founders with the right mindset "
            "and problem, not just a polished deck."
        ),
    )
    good_fit_items = RichTextField(
        help_text="Bullet list of reasons a founder IS a good fit. Use <ul><li> tags.",
        default="",
        blank=True,
    )
    not_good_fit_label = models.CharField(
        max_length=100,
        default="Not a good fit",
        help_text="Heading shown above the 'not a good fit' list, e.g. 'Not a good fit'",
    )
    not_good_fit_items = RichTextField(
        help_text="Bullet list of reasons a founder is NOT a good fit. Use <ul><li> tags.",
        default="",
        blank=True,
    )
    look_for_section_title = models.CharField(
        max_length=200,
        default="What we look for in an application",
        help_text="Heading of the criteria card on the right side of the 'Who Should Apply' section.",
    )

    # ── Application process ───────────────────────────────────────────────────
    process_section_subtitle = models.CharField(
        max_length=200,
        default="Four simple steps. The whole process takes less than 30 minutes.",
    )

    # ── Program description (rich text body) ──────────────────────────────────
    title = models.CharField(max_length=200, default="LaunchPadi Accelerator Program")
    program_description = RichTextField(blank=True, default="")
    image = models.ImageField(upload_to='accelerator/', blank=True)

    # ── Application sidebar / status ──────────────────────────────────────────
    application_info = RichTextField(
        help_text="Short text shown in the sidebar above the deadline and apply button.",
        blank=True,
        default="",
    )
    application_deadline = models.DateTimeField(null=True, blank=True)
    is_accepting_applications = models.BooleanField(default=True)

    # ── Bottom CTA ────────────────────────────────────────────────────────────
    cta_title_open = models.CharField(max_length=200, default="Ready to apply?")
    cta_body_open = models.TextField(
        default="Applications are open now. It takes about 20 minutes. There's nothing to lose.",
    )
    cta_title_closed = models.CharField(max_length=200, default="Interested in the next cohort?")
    cta_body_closed = models.TextField(
        default=(
            "Applications are closed for this cycle. Join the waitlist and we'll notify you "
            "the moment the next cohort opens."
        ),
    )

    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Incubator / Accelerator Page"
        verbose_name_plural = "Incubator / Accelerator Page Settings"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class ProgramPillar(models.Model):
    page = models.ForeignKey(
        IncubatorAcceleratorPage,
        on_delete=models.CASCADE,
        related_name='pillars',
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    icon_class = models.CharField(
        max_length=100,
        default="fas fa-star",
        help_text="FontAwesome icon class, e.g. 'fas fa-graduation-cap'",
    )
    icon_color = models.CharField(
        max_length=30,
        default="#26af59",
        help_text="CSS color for the icon, e.g. '#26af59'",
    )
    bg_color = models.CharField(
        max_length=60,
        default="rgba(38,175,89,0.1)",
        help_text="CSS background for the icon box, e.g. 'rgba(38,175,89,0.1)'",
    )
    cta_text = models.CharField(max_length=100, blank=True, default="")
    cta_url = models.CharField(max_length=200, blank=True, default="")
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']
        verbose_name = "Program Pillar"
        verbose_name_plural = "Program Pillars"

    def __str__(self):
        return self.title


class ApplicationStep(models.Model):
    page = models.ForeignKey(
        IncubatorAcceleratorPage,
        on_delete=models.CASCADE,
        related_name='steps',
    )
    step_number = models.PositiveIntegerField()
    title = models.CharField(max_length=200)
    description = models.TextField()
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'step_number']
        verbose_name = "Application Step"
        verbose_name_plural = "Application Steps"

    def __str__(self):
        return f"Step {self.step_number}: {self.title}"


class WhatWeLookForItem(models.Model):
    page = models.ForeignKey(
        IncubatorAcceleratorPage,
        on_delete=models.CASCADE,
        related_name='look_for_items',
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    icon_class = models.CharField(
        max_length=100,
        default="fas fa-check",
        help_text="FontAwesome icon class",
    )
    icon_color = models.CharField(max_length=30, default="#26af59")
    bg_color = models.CharField(max_length=60, default="rgba(38,175,89,0.1)")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name = "What We Look For"
        verbose_name_plural = "What We Look For (criteria)"

    def __str__(self):
        return self.title


class IncubatorApplication(models.Model):
    project = models.CharField(max_length=200, default='')
    applicant_name = models.CharField(max_length=200, default='')
    applicant_email = models.EmailField(default='')
    applicant_phone = models.CharField(max_length=20, blank=True, default='')
    applicant_company = models.CharField(max_length=200, blank=True, default='')

    website = models.URLField(blank=True, default='www.website.com')
    stage = models.CharField(
        max_length=50,
        choices=[
            ('idea', 'Idea Stage'),
            ('mvp', 'Minimum Viable Product'),
            ('launched', 'Launched'),
            ('growing', 'Growing/Scaling'),
        ],
        default='idea',
    )
    industry = models.CharField(max_length=100, default='', help_text="e.g. FinTech, AgriTech, HealthTech")

    application_text = RichTextField(blank=True, default='', help_text="Describe your startup and what problem it solves")
    traction = RichTextField(blank=True, default='', help_text="Mention any traction, pilot users, revenue, etc.")
    team_background = RichTextField(blank=True, default='', help_text="Tell us about your team and why you're the right people to build this")
    goals_for_program = models.TextField(blank=True, default='', help_text="What do you hope to achieve during the accelerator?")
    funding_raised = models.CharField(max_length=100, blank=True, default='', help_text="e.g. $10,000 in grants, $5,000 from friends & family")
    funding_needed = models.CharField(max_length=100, blank=True, default='', help_text="How much are you looking to raise post-program?")

    pitch_deck = models.FileField(upload_to='pitch_decks/', default='', blank=True, help_text="Upload your pitch deck (PDF, max 10MB)")

    application_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
            ('waitlisted', 'Waitlisted'),
        ],
        default='pending',
    )
    reviewed = models.BooleanField(default=False)

    def __str__(self):
        return f"Application for {self.project} by {self.applicant_name}"
