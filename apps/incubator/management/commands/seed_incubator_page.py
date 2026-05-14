from django.core.management.base import BaseCommand
from apps.incubator.models import (
    IncubatorAcceleratorPage,
    ProgramPillar,
    ApplicationStep,
    WhatWeLookForItem,
)

PILLARS = [
    {
        'order': 1,
        'title': '12-Week Curriculum',
        'description': (
            'A structured, self-paced program covering every aspect of early-stage company building — '
            'from problem discovery to pitching investors. 48+ lessons, exercises, and deliverables.'
        ),
        'icon_class': 'fas fa-graduation-cap',
        'icon_color': '#26af59',
        'bg_color': 'rgba(38,175,89,0.1)',
        'cta_text': 'View curriculum',
        'cta_url': '/lms/',
    },
    {
        'order': 2,
        'title': 'Expert Mentorship',
        'description': (
            'Regular 1-on-1 and group sessions with operators, investors, and founders who\'ve built '
            'in Nigeria. Real advice, not generic theory.'
        ),
        'icon_class': 'fas fa-user-tie',
        'icon_color': '#2563eb',
        'bg_color': 'rgba(37,99,235,0.1)',
        'cta_text': '',
        'cta_url': '',
    },
    {
        'order': 3,
        'title': 'Cohort Community',
        'description': (
            'You\'ll build alongside a cohort of carefully selected founders at a similar stage. '
            'Peer accountability, collaboration, and relationships that outlast the program.'
        ),
        'icon_class': 'fas fa-users',
        'icon_color': '#7c3aed',
        'bg_color': 'rgba(124,58,237,0.1)',
        'cta_text': '',
        'cta_url': '',
    },
    {
        'order': 4,
        'title': 'Demo Day & Funding',
        'description': (
            'The program ends with Demo Day — a curated pitch event in front of investors, angels, '
            'and corporate partners. The best teams get direct investment consideration.'
        ),
        'icon_class': 'fas fa-trophy',
        'icon_color': '#d97706',
        'bg_color': 'rgba(217,119,6,0.1)',
        'cta_text': '',
        'cta_url': '',
    },
]

STEPS = [
    {
        'order': 1,
        'step_number': 1,
        'title': 'Submit Application',
        'description': 'Fill in the short online form — your background, problem, and why you\'re building this.',
    },
    {
        'order': 2,
        'step_number': 2,
        'title': 'Initial Review',
        'description': 'Our team reviews every application. You\'ll hear back within 7 days of the deadline.',
    },
    {
        'order': 3,
        'step_number': 3,
        'title': 'Founder Conversation',
        'description': 'Shortlisted founders get a 20-minute video call with the LaunchPadi team.',
    },
    {
        'order': 4,
        'step_number': 4,
        'title': 'Cohort Acceptance',
        'description': 'Selected founders receive their offer and onboarding details. Day 1 begins!',
    },
]

LOOK_FOR = [
    {
        'order': 1,
        'title': 'Genuine problem insight',
        'description': (
            'You\'ve experienced or deeply researched the problem. You understand who has it '
            'and why it hasn\'t been solved.'
        ),
        'icon_class': 'fas fa-lightbulb',
        'icon_color': '#26af59',
        'bg_color': 'rgba(38,175,89,0.1)',
    },
    {
        'order': 2,
        'title': 'Founder conviction',
        'description': (
            'We care more about your "why" than how polished your idea is. '
            'Tell us what keeps you up at night.'
        ),
        'icon_class': 'fas fa-fire',
        'icon_color': '#2563eb',
        'bg_color': 'rgba(37,99,235,0.1)',
    },
    {
        'order': 3,
        'title': 'Team or commitment to build one',
        'description': (
            'Solo founders are welcome. We look at your plan for building the team '
            'you need to execute.'
        ),
        'icon_class': 'fas fa-users',
        'icon_color': '#7c3aed',
        'bg_color': 'rgba(124,58,237,0.1)',
    },
    {
        'order': 4,
        'title': 'Nigerian / African market focus',
        'description': (
            'We build programs and networks specifically for the African ecosystem. '
            'Your idea should be relevant to this context.'
        ),
        'icon_class': 'fas fa-map-marker-alt',
        'icon_color': '#d97706',
        'bg_color': 'rgba(217,119,6,0.1)',
    },
]

GOOD_FIT = """<ul>
<li>You have a problem you're deeply passionate about solving in Nigeria or Africa</li>
<li>You're at the idea or early-MVP stage (pre-revenue or early traction)</li>
<li>You can commit 5–8 hours per week to the program</li>
<li>You're coachable and willing to challenge your own assumptions</li>
<li>You're based in Nigeria or building for the Nigerian/African market</li>
<li>You want structure, accountability, and a community — not just content</li>
</ul>"""

NOT_FIT = """<ul>
<li>Series A or later-stage startups</li>
<li>Freelancers or service businesses without a scalable product</li>
<li>Founders not willing to commit time or take feedback</li>
</ul>"""

APPLICATION_INFO = """<p>LaunchPadi runs cohort-based programs for idea and early-MVP stage founders in Nigeria.
Apply now and join the next cohort of ambitious builders.</p>"""

PROGRAM_DESCRIPTION = """<p>LaunchPadi is StartUpRipple's flagship founder development program, built specifically for Nigerian
entrepreneurs at the earliest stage of their startup journey.</p>

<p>Unlike generic online courses, LaunchPadi is a cohort-based experience — meaning you go through the program alongside
a carefully selected group of peers, with structured accountability, real mentors, and a Demo Day at the end.</p>

<h3>What makes LaunchPadi different?</h3>
<ul>
<li><strong>Built for Nigeria:</strong> Every module, example, and exercise is designed with the Nigerian and African
market context in mind. No copy-pasted Silicon Valley advice.</li>
<li><strong>Cohort accountability:</strong> You're not learning alone. Your cohort becomes your peer advisory board,
sounding board, and sometimes your co-founder network.</li>
<li><strong>Real deliverables:</strong> Each week you produce something tangible — a customer persona, a business model
canvas, a financial projection. By Demo Day you have a full founder portfolio.</li>
<li><strong>Mentor access:</strong> You get direct time with operators and investors who understand your market.</li>
</ul>

<h3>Program structure</h3>
<p>The program runs for 12 weeks. Weeks 1–11 are curriculum-led with weekly cohort check-ins. Week 12 is Demo Day
preparation and the pitch event itself.</p>"""


class Command(BaseCommand):
    help = 'Seed the IncubatorAcceleratorPage with all default content'

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true', help='Delete existing pillars/steps/criteria before seeding')

    def handle(self, *args, **options):
        page = IncubatorAcceleratorPage.load()

        page.hero_title = "Build Your Idea Into a Business — With the Right Support"
        page.hero_subtitle = (
            "A cohort-based accelerator for Nigerian founders at the idea and early-MVP stage. "
            "Curriculum. Mentorship. Community. A real chance at funding."
        )
        page.stat_weeks = "12"
        page.stat_lessons = "48+"
        page.stat_mentorship = "1:1"
        page.stat_event = "Demo Day"
        page.stat_cost = "Free"

        page.pillars_section_title = "Four pillars. One transformative program."
        page.pillars_section_subtitle = (
            "LaunchPadi isn't just a course — it's a complete founder development experience "
            "built for the Nigerian ecosystem."
        )

        page.curriculum_section_title = "One module per week. Built for idea-stage founders."
        page.curriculum_section_subtitle = (
            "Each week covers a new building block of your startup — with lessons, "
            "a practical exercise, and a deliverable you keep after the program."
        )

        page.who_section_title = "You're the right fit if…"
        page.who_section_intro = (
            "LaunchPadi is highly selective. We look for founders with the right mindset "
            "and problem, not just a polished deck."
        )
        page.good_fit_items = GOOD_FIT
        page.not_good_fit_label = "Not a good fit"
        page.not_good_fit_items = NOT_FIT
        page.look_for_section_title = "What we look for in an application"

        page.process_section_subtitle = "Four simple steps. The whole process takes less than 30 minutes."

        page.title = "LaunchPadi Accelerator Program"
        page.program_description = PROGRAM_DESCRIPTION
        page.application_info = APPLICATION_INFO

        page.cta_title_open = "Ready to apply?"
        page.cta_body_open = "Applications are open now. It takes about 20 minutes. There's nothing to lose."
        page.cta_title_closed = "Interested in the next cohort?"
        page.cta_body_closed = (
            "Applications are closed for this cycle. Join the waitlist and we'll notify you "
            "the moment the next cohort opens."
        )
        page.save()
        self.stdout.write("✓ Page settings saved")

        if options['reset']:
            ProgramPillar.objects.filter(page=page).delete()
            ApplicationStep.objects.filter(page=page).delete()
            WhatWeLookForItem.objects.filter(page=page).delete()
            self.stdout.write("  ↻ Existing pillars/steps/criteria cleared")

        for data in PILLARS:
            ProgramPillar.objects.update_or_create(
                page=page, title=data['title'],
                defaults={k: v for k, v in data.items() if k != 'title'},
            )
        self.stdout.write(f"✓ {len(PILLARS)} program pillars seeded")

        for data in STEPS:
            ApplicationStep.objects.update_or_create(
                page=page, step_number=data['step_number'],
                defaults={k: v for k, v in data.items() if k != 'step_number'},
            )
        self.stdout.write(f"✓ {len(STEPS)} application steps seeded")

        for data in LOOK_FOR:
            WhatWeLookForItem.objects.update_or_create(
                page=page, title=data['title'],
                defaults={k: v for k, v in data.items() if k != 'title'},
            )
        self.stdout.write(f"✓ {len(LOOK_FOR)} 'what we look for' criteria seeded")

        self.stdout.write(self.style.SUCCESS("\nDone! Incubator page fully seeded."))
