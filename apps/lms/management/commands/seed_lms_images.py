import requests
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from apps.lms.models import LMSModule

# Curated Unsplash photos, one per week topic. Using ?w=900&h=500&fit=crop&q=80 for consistent size.
WEEK_IMAGES = {
    1:  ("photo-1519085360753-af0119f7cbe7", "wk1_founder_mindset.jpg"),       # determined entrepreneur
    2:  ("photo-1454165804606-c3d57bc86b40", "wk2_problem_discovery.jpg"),     # whiteboard research session
    3:  ("photo-1551288049-bebda4e38f71",   "wk3_market_research.jpg"),        # data dashboard / analytics
    4:  ("photo-1529156069898-49953e39b3ac", "wk4_customer_segments.jpg"),     # diverse group of people
    5:  ("photo-1531403009284-440f080d1e12", "wk5_mvp_design.jpg"),            # UX wireframing on screen
    6:  ("photo-1611974789855-9c2a0a7236a3", "wk6_business_model.jpg"),        # financial charts / business plan
    7:  ("photo-1558655146-d09347e92766",   "wk7_brand_identity.jpg"),         # creative branding mood board
    8:  ("photo-1460925895917-afdab827c52f", "wk8_go_to_market.jpg"),          # laptop strategy / metrics
    9:  ("photo-1498050108023-c5249f4df085", "wk9_product_dev.jpg"),           # developer coding on laptop
    10: ("photo-1554224155-6726b3ff858f",   "wk10_finance.jpg"),               # coins & financial planning
    11: ("photo-1475721027785-f74eccf877e2", "wk11_pitching.jpg"),             # speaker on stage / presentation
    12: ("photo-1505373877841-8d25f7d46678", "wk12_demo_day.jpg"),             # celebration / finish line
}

BASE_URL = "https://images.unsplash.com/{photo_id}?w=900&h=500&fit=crop&q=80&auto=format"


class Command(BaseCommand):
    help = "Download and assign stock cover images to LMS modules"

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Re-download and overwrite images even if already set',
        )

    def handle(self, *args, **options):
        force = options['force']
        modules = LMSModule.objects.all().order_by('week_number')

        if not modules.exists():
            self.stderr.write("No LMS modules found. Run seed_lms_content first.")
            return

        for module in modules:
            week = module.week_number
            if week not in WEEK_IMAGES:
                self.stdout.write(self.style.WARNING(f"  Week {week}: no image configured, skipping"))
                continue

            if module.cover_image and not force:
                self.stdout.write(f"  Week {week}: already has image, skipping (use --force to overwrite)")
                continue

            photo_id, filename = WEEK_IMAGES[week]
            url = BASE_URL.format(photo_id=photo_id)

            self.stdout.write(f"  Week {week}: downloading {filename} ...", ending='')

            try:
                resp = requests.get(url, timeout=30)
                resp.raise_for_status()
                content = ContentFile(resp.content, name=filename)
                module.cover_image.save(filename, content, save=True)
                self.stdout.write(self.style.SUCCESS(" done"))
            except requests.RequestException as e:
                self.stdout.write(self.style.ERROR(f" FAILED: {e}"))

        self.stdout.write(self.style.SUCCESS("\nAll done."))
