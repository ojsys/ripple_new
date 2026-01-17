"""
Management command to seed homepage content.
"""
from django.core.management.base import BaseCommand
from apps.cms.models import HomePage, HowItWorksStep, Testimonial


class Command(BaseCommand):
    help = 'Seeds the homepage with initial content'

    def handle(self, *args, **options):
        self.stdout.write('Seeding homepage content...')

        # Create or update HomePage
        homepage, created = HomePage.objects.get_or_create(pk=1)

        if created:
            self.stdout.write(self.style.SUCCESS('Created HomePage instance'))
        else:
            self.stdout.write('HomePage already exists, updating...')

        # Update with comprehensive content
        homepage.hero_title = "Empowering Africa's Next Generation of Innovators"
        homepage.hero_subtitle = "StartUpRipple connects visionary founders with investors, donors, and strategic partners. Launch your crowdfunding campaign, invest through our unique SRT token system, or join our accelerator program to scale your startup."
        homepage.hero_cta_primary_text = "Explore Projects"
        homepage.hero_cta_primary_url = "/projects/"
        homepage.hero_cta_secondary_text = "Start a Project"
        homepage.hero_cta_secondary_url = "/accounts/signup/"

        # Stats
        homepage.stat_1_value = "$2.5M+"
        homepage.stat_1_label = "Total Funded"
        homepage.stat_2_value = "150+"
        homepage.stat_2_label = "Projects Launched"
        homepage.stat_3_value = "5,000+"
        homepage.stat_3_label = "Active Backers"
        homepage.stat_4_value = "12"
        homepage.stat_4_label = "African Countries"

        # How It Works
        homepage.how_it_works_title = "How StartUpRipple Works"
        homepage.how_it_works_subtitle = "Our platform makes it simple to fund innovation or find funding for your startup. Here's how it works for everyone."

        # Featured Projects
        homepage.featured_projects_title = "Trending Projects"
        homepage.featured_projects_subtitle = "Discover the most exciting startups currently seeking funding on our platform"

        # SRT Section
        homepage.srt_title = "StartUp Ripple Tokens (SRT)"
        homepage.srt_subtitle = "A smarter way to invest in Africa's most promising startups"
        homepage.srt_description = """
        <p>SRT tokens represent a revolutionary approach to startup investment. As a partner, you can:</p>
        <ul>
            <li>Purchase token packages that fit your investment goals</li>
            <li>Invest tokens across a diversified portfolio of vetted ventures</li>
            <li>Track your investments and returns in real-time</li>
            <li>Benefit from our expert curation and due diligence</li>
        </ul>
        <p>Join hundreds of partners already building wealth while supporting African innovation.</p>
        """
        homepage.srt_cta_text = "Become a Partner"
        homepage.srt_cta_url = "/accounts/signup/"

        # Incubator Section
        homepage.incubator_title = "StartUpRipple Accelerator"
        homepage.incubator_subtitle = "Launch and scale your startup with expert guidance"
        homepage.incubator_description = """
        <p>Our 12-week intensive accelerator program is designed to take early-stage African startups to the next level. We provide:</p>
        <ul>
            <li>Hands-on mentorship from successful entrepreneurs and industry experts</li>
            <li>Seed funding of up to $50,000 for qualifying startups</li>
            <li>Access to our network of investors, partners, and potential customers</li>
            <li>Dedicated workspace and essential business resources</li>
        </ul>
        """
        homepage.incubator_cta_text = "Apply Now"
        homepage.incubator_cta_url = "/incubator/apply/"

        # Testimonials
        homepage.testimonials_title = "Success Stories"
        homepage.testimonials_subtitle = "Hear from founders and investors who've found success on our platform"

        # Partners
        homepage.partners_title = "Trusted By Leading Organizations"

        # CTA
        homepage.cta_title = "Ready to Make an Impact?"
        homepage.cta_subtitle = "Join thousands of founders and investors building the future of African innovation"
        homepage.cta_primary_text = "Get Started Today"
        homepage.cta_primary_url = "/accounts/signup/"
        homepage.cta_secondary_text = "Learn More"
        homepage.cta_secondary_url = "/cms/about/"

        # Newsletter
        homepage.newsletter_title = "Stay in the Loop"
        homepage.newsletter_subtitle = "Get weekly updates on new projects, investment opportunities, and startup news"

        homepage.save()
        self.stdout.write(self.style.SUCCESS('Updated HomePage content'))

        # Create How It Works Steps
        steps_data = [
            {
                'icon': 'fas fa-user-plus',
                'title': 'Create Your Account',
                'description': 'Sign up in minutes as a founder, investor, donor, or SRT partner. Complete your profile to get started.',
                'order': 1
            },
            {
                'icon': 'fas fa-lightbulb',
                'title': 'Launch or Discover',
                'description': 'Founders can create compelling campaigns. Investors and donors can explore innovative projects seeking funding.',
                'order': 2
            },
            {
                'icon': 'fas fa-hand-holding-usd',
                'title': 'Fund & Invest',
                'description': 'Support projects through donations, equity investments, or SRT tokens. Every contribution makes a difference.',
                'order': 3
            },
            {
                'icon': 'fas fa-chart-line',
                'title': 'Grow Together',
                'description': 'Track progress, receive updates, and watch startups succeed. Investors earn returns as companies grow.',
                'order': 4
            },
        ]

        # Clear existing steps and create new ones
        homepage.how_it_works_steps.all().delete()
        for step_data in steps_data:
            HowItWorksStep.objects.create(homepage=homepage, **step_data)

        self.stdout.write(self.style.SUCCESS(f'Created {len(steps_data)} How It Works steps'))

        # Create sample testimonials if none exist
        if not Testimonial.objects.exists():
            testimonials_data = [
                {
                    'name': 'Adaeze Okonkwo',
                    'position': 'Founder & CEO',
                    'company': 'GreenHarvest AgriTech',
                    'content': 'StartUpRipple helped us raise our seed round in just 6 weeks. The platform made it easy to connect with investors who truly understood our vision for sustainable agriculture in Nigeria.',
                    'rating': 5,
                    'is_active': True
                },
                {
                    'name': 'David Mensah',
                    'position': 'SRT Partner',
                    'company': 'Angel Investor',
                    'content': 'The SRT token system is brilliant. I can diversify my investments across multiple vetted startups without the complexity of traditional VC deals. My portfolio has grown 40% in the first year.',
                    'rating': 5,
                    'is_active': True
                },
                {
                    'name': 'Fatima Hassan',
                    'position': 'Co-founder',
                    'company': 'EduTech Solutions',
                    'content': 'The accelerator program transformed our startup. The mentorship, funding, and network access were invaluable. We went from idea to 10,000 users in just 4 months.',
                    'rating': 5,
                    'is_active': True
                },
                {
                    'name': 'Oluwaseun Adeleke',
                    'position': 'Donor',
                    'company': 'Tech Professional',
                    'content': 'I love supporting African innovation through StartUpRipple. The platform makes it easy to find projects I care about and track how my contributions make an impact.',
                    'rating': 4,
                    'is_active': True
                },
                {
                    'name': 'Amara Diallo',
                    'position': 'Founder',
                    'company': 'HealthConnect',
                    'content': 'From application to funding, the entire process was smooth and transparent. StartUpRipple\'s team provided guidance every step of the way. Highly recommended!',
                    'rating': 5,
                    'is_active': True
                },
                {
                    'name': 'Kwame Asante',
                    'position': 'Investor',
                    'company': 'Venture Capital',
                    'content': 'The quality of startups on StartUpRipple is impressive. The due diligence process gives me confidence in the opportunities, and the platform makes investment management effortless.',
                    'rating': 5,
                    'is_active': True
                },
            ]

            for testimonial_data in testimonials_data:
                Testimonial.objects.create(**testimonial_data)

            self.stdout.write(self.style.SUCCESS(f'Created {len(testimonials_data)} testimonials'))
        else:
            self.stdout.write('Testimonials already exist, skipping...')

        self.stdout.write(self.style.SUCCESS('Homepage seeding complete!'))
