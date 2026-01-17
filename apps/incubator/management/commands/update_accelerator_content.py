from django.core.management.base import BaseCommand
from apps.incubator.models import IncubatorAcceleratorPage
from django.utils.dateparse import parse_datetime

class Command(BaseCommand):
    help = 'Creates or updates the Incubator/Accelerator page content from a predefined source.'

    def handle(self, *args, **options):
        self.stdout.write('Updating Incubator/Accelerator page content...')

        # Get or create the page instance
        page, created = IncubatorAcceleratorPage.objects.get_or_create(id=1)

        # --- Extracted Content ---
        title = "Founders LaunchPadi"

        program_description = """
        <p class="lead">The Founders LaunchPadi is a 1-week intensive program designed for very early-stage founders who are ready to take their idea seriously—and position it for growth, investment, and real-world traction.</p>
        <p>This is not a retreat. It’s a sprint. We help founders move from “interesting idea” to “fundable venture” by compressing the most critical startup building blocks into a focused, practical, and brutally honest experience.</p>
        <h4 class="mt-4">Who Should Apply?</h4>
        <ul>
            <li>Early-stage founders (idea to MVP stage)</li>
            <li>Builders without buzzwords</li>
            <li>Teams ready to validate fast and listen hard</li>
            <li>People outside major cities looking for real access to capital</li>
        </ul>
        """

        key_stages = """
        <div class="timeline-item">
            <div class="timeline-marker"></div>
            <h5 class="mb-1">Startup Fundamentals</h5>
            <p class="text-muted">What makes ventures succeed—and why most fail.</p>
        </div>
        <div class="timeline-item">
            <div class="timeline-marker"></div>
            <h5 class="mb-1">Problem-Solution Fit</h5>
            <p class="text-muted">How to identify and articulate a real market need.</p>
        </div>
        <div class="timeline-item">
            <div class="timeline-marker"></div>
            <h5 class="mb-1">Business Models & Early Traction</h5>
            <p class="text-muted">Choosing a revenue engine, customer discovery, and MVP thinking.</p>
        </div>
        <div class="timeline-item">
            <div class="timeline-marker"></div>
            <h5 class="mb-1">Investor Readiness</h5>
            <p class="text-muted">How to pitch, raise, and not embarrass yourself.</p>
        </div>
        <div class="timeline-item">
            <div class="timeline-marker"></div>
            <h5 class="mb-1">Platform Onboarding & Demo Day</h5>
            <p class="text-muted">Launch your startup to a live investor community and pitch to a panel of investors.</p>
        </div>
        """

        key_benefits = """
        <ul class="list-unstyled">
            <li class="mb-2"><i class="fas fa-check-circle text-success me-2"></i>A sharpened business model</li>
            <li class="mb-2"><i class="fas fa-check-circle text-success me-2"></i>A pitch-ready deck</li>
            <li class="mb-2"><i class="fas fa-check-circle text-success me-2"></i>A clear understanding of your funding path</li>
            <li class="mb-2"><i class="fas fa-check-circle text-success me-2"></i>Direct access to the StartUpRipples platform</li>
            <li class="mb-2"><i class="fas fa-check-circle text-success me-2"></i>Mentorship & community support post-program</li>
        </ul>
        """
        
        application_info = "<p>Submit your application to be considered for our next physical cohort starting in Jos, Nigeria. The program is a full-day, 5-day sprint from Monday to Friday, culminating in a Demo Day.</p>"
        
        application_deadline = parse_datetime("2025-07-18T23:59:59Z")
        
        is_accepting_applications = False

        # --- Update Page Fields ---
        page.title = title
        page.program_description = program_description
        page.key_stages = key_stages
        page.key_benefits = key_benefits
        page.application_info = application_info
        page.application_deadline = application_deadline
        page.is_accepting_applications = is_accepting_applications
        
        # A default image if none is set
        # page.image.name = 'path/to/default/image.jpg'

        page.save()

        self.stdout.write(self.style.SUCCESS('Successfully updated the Incubator/Accelerator page content.'))
