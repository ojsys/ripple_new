"""
Management command to seed sample projects with categories and funding types.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from apps.projects.models import Project, Category, FundingType, Reward
from apps.cms.models import HeroSlider
from apps.accounts.models import CustomUser


class Command(BaseCommand):
    help = 'Seeds sample projects, categories, funding types, and hero sliders'

    def handle(self, *args, **options):
        self.stdout.write('Seeding sample data...')

        # Create Categories
        categories_data = [
            'Technology',
            'Agriculture',
            'Healthcare',
            'Education',
            'FinTech',
            'Clean Energy',
            'E-Commerce',
            'Social Impact',
        ]

        for cat_name in categories_data:
            category, created = Category.objects.get_or_create(name=cat_name)
            if created:
                self.stdout.write(f'  Created category: {category.name}')

        self.stdout.write(self.style.SUCCESS(f'Categories: {Category.objects.count()}'))

        # Create Funding Types
        funding_types_data = [
            {'name': 'Donation', 'description': 'Charitable donations with no equity'},
            {'name': 'Equity', 'description': 'Investment in exchange for company shares'},
            {'name': 'Reward', 'description': 'Contribution in exchange for rewards/perks'},
            {'name': 'Debt', 'description': 'Loan-based funding with interest'},
        ]

        for ft_data in funding_types_data:
            funding_type, created = FundingType.objects.get_or_create(
                name=ft_data['name'],
                defaults={'description': ft_data['description']}
            )
            if created:
                self.stdout.write(f'  Created funding type: {funding_type.name}')

        self.stdout.write(self.style.SUCCESS(f'Funding Types: {FundingType.objects.count()}'))

        # Create or get a sample user for projects
        founder_user, created = CustomUser.objects.get_or_create(
            email='founder@startupripple.com',
            defaults={
                'first_name': 'Demo',
                'last_name': 'Founder',
                'user_type': 'founder',
                'is_active': True,
            }
        )
        if created:
            founder_user.set_password('demo12345')
            founder_user.save()
            self.stdout.write(f'  Created demo founder user: {founder_user.email}')

        # Get references
        tech_cat = Category.objects.get(name='Technology')
        agri_cat = Category.objects.get(name='Agriculture')
        health_cat = Category.objects.get(name='Healthcare')
        edu_cat = Category.objects.get(name='Education')
        fintech_cat = Category.objects.get(name='FinTech')
        clean_cat = Category.objects.get(name='Clean Energy')

        donation_type = FundingType.objects.get(name='Donation')
        equity_type = FundingType.objects.get(name='Equity')
        reward_type = FundingType.objects.get(name='Reward')

        # Create Sample Projects
        projects_data = [
            {
                'title': 'AgroConnect - Smart Farming Platform',
                'short_description': 'Connecting African farmers with markets, financing, and agricultural insights through mobile technology.',
                'description': '''
                    <h3>About AgroConnect</h3>
                    <p>AgroConnect is a revolutionary mobile platform designed to transform agriculture across Africa. We connect smallholder farmers directly with buyers, eliminating middlemen and ensuring fair prices.</p>

                    <h4>Key Features</h4>
                    <ul>
                        <li><strong>Market Access:</strong> Direct connection to buyers and commodity markets</li>
                        <li><strong>Weather Insights:</strong> Localized weather forecasts and farming advice</li>
                        <li><strong>Micro-financing:</strong> Access to agricultural loans and insurance</li>
                        <li><strong>Knowledge Hub:</strong> Best practices and crop management guides</li>
                    </ul>

                    <h4>Impact</h4>
                    <p>We've already helped over 5,000 farmers increase their income by an average of 40%. With your support, we can reach 100,000 farmers by 2025.</p>
                ''',
                'funding_goal': Decimal('50000.00'),
                'amount_raised': Decimal('32500.00'),
                'deadline': timezone.now() + timedelta(days=45),
                'category': agri_cat,
                'funding_type': equity_type,
                'location': 'Nairobi, Kenya',
                'status': 'approved',
            },
            {
                'title': 'MediLink - Telemedicine for Rural Africa',
                'short_description': 'Bringing quality healthcare to underserved communities through AI-powered telemedicine.',
                'description': '''
                    <h3>Healthcare Without Borders</h3>
                    <p>MediLink bridges the healthcare gap in rural Africa by connecting patients with qualified doctors through our innovative telemedicine platform.</p>

                    <h4>Our Solution</h4>
                    <ul>
                        <li><strong>Video Consultations:</strong> Connect with doctors from anywhere</li>
                        <li><strong>AI Symptom Checker:</strong> Preliminary health assessments</li>
                        <li><strong>E-Prescriptions:</strong> Digital prescriptions sent to local pharmacies</li>
                        <li><strong>Health Records:</strong> Secure digital health records</li>
                    </ul>

                    <h4>The Problem</h4>
                    <p>Over 50% of rural Africans live more than 5km from a health facility. MediLink brings the doctor to them.</p>
                ''',
                'funding_goal': Decimal('75000.00'),
                'amount_raised': Decimal('45000.00'),
                'deadline': timezone.now() + timedelta(days=60),
                'category': health_cat,
                'funding_type': equity_type,
                'location': 'Lagos, Nigeria',
                'status': 'approved',
            },
            {
                'title': 'EduSpark - Affordable Online Learning',
                'short_description': 'Making quality education accessible to every African child through interactive online courses.',
                'description': '''
                    <h3>Education for All</h3>
                    <p>EduSpark is on a mission to democratize education across Africa. Our platform offers curriculum-aligned courses that work even on low-bandwidth connections.</p>

                    <h4>What We Offer</h4>
                    <ul>
                        <li><strong>Offline Mode:</strong> Download lessons to learn without internet</li>
                        <li><strong>Local Languages:</strong> Content in 15+ African languages</li>
                        <li><strong>Interactive Lessons:</strong> Engaging video and quiz content</li>
                        <li><strong>Progress Tracking:</strong> Monitor learning achievements</li>
                    </ul>

                    <h4>Our Impact</h4>
                    <p>Students using EduSpark have shown a 35% improvement in exam scores. Help us reach 1 million students!</p>
                ''',
                'funding_goal': Decimal('40000.00'),
                'amount_raised': Decimal('28000.00'),
                'deadline': timezone.now() + timedelta(days=30),
                'category': edu_cat,
                'funding_type': donation_type,
                'location': 'Accra, Ghana',
                'status': 'approved',
            },
            {
                'title': 'PaySwift - Mobile Payment Revolution',
                'short_description': 'Seamless cross-border payments and remittances for African businesses and diaspora.',
                'description': '''
                    <h3>Borderless Payments</h3>
                    <p>PaySwift enables instant, low-cost money transfers across Africa and to the diaspora. Send money home in seconds, not days.</p>

                    <h4>Features</h4>
                    <ul>
                        <li><strong>Instant Transfers:</strong> Money arrives in seconds</li>
                        <li><strong>Low Fees:</strong> Up to 80% cheaper than traditional banks</li>
                        <li><strong>Multi-Currency:</strong> Support for 20+ African currencies</li>
                        <li><strong>Business Tools:</strong> Invoicing and payment tracking</li>
                    </ul>
                ''',
                'funding_goal': Decimal('100000.00'),
                'amount_raised': Decimal('67000.00'),
                'deadline': timezone.now() + timedelta(days=90),
                'category': fintech_cat,
                'funding_type': equity_type,
                'location': 'Johannesburg, South Africa',
                'status': 'approved',
            },
            {
                'title': 'SolarHome - Clean Energy for Every Home',
                'short_description': 'Affordable solar home systems bringing clean, reliable electricity to off-grid communities.',
                'description': '''
                    <h3>Power to the People</h3>
                    <p>SolarHome provides pay-as-you-go solar systems that enable families to afford clean energy through small daily payments.</p>

                    <h4>Our Systems</h4>
                    <ul>
                        <li><strong>Solar Panels:</strong> High-efficiency panels with 25-year warranty</li>
                        <li><strong>Battery Storage:</strong> Store power for nighttime use</li>
                        <li><strong>Smart Metering:</strong> Pay only for what you use</li>
                        <li><strong>Appliance Financing:</strong> Add TVs, fans, and more</li>
                    </ul>

                    <h4>Environmental Impact</h4>
                    <p>Each system saves 1.5 tons of CO2 annually compared to kerosene lamps.</p>
                ''',
                'funding_goal': Decimal('80000.00'),
                'amount_raised': Decimal('52000.00'),
                'deadline': timezone.now() + timedelta(days=75),
                'category': clean_cat,
                'funding_type': reward_type,
                'location': 'Kampala, Uganda',
                'status': 'approved',
            },
            {
                'title': 'TechTalent - African Developer Academy',
                'short_description': 'Training the next generation of African software developers with job-guaranteed bootcamps.',
                'description': '''
                    <h3>Building Africa\'s Tech Future</h3>
                    <p>TechTalent runs intensive coding bootcamps that transform beginners into job-ready software developers in just 16 weeks.</p>

                    <h4>Our Program</h4>
                    <ul>
                        <li><strong>Full-Stack Training:</strong> Web, mobile, and cloud development</li>
                        <li><strong>Job Guarantee:</strong> Get hired or get your money back</li>
                        <li><strong>Income Sharing:</strong> Pay only when you get a job</li>
                        <li><strong>Career Support:</strong> Resume building and interview prep</li>
                    </ul>

                    <h4>Results</h4>
                    <p>92% job placement rate with an average starting salary of $24,000.</p>
                ''',
                'funding_goal': Decimal('60000.00'),
                'amount_raised': Decimal('15000.00'),
                'deadline': timezone.now() + timedelta(days=120),
                'category': tech_cat,
                'funding_type': donation_type,
                'location': 'Kigali, Rwanda',
                'status': 'approved',
            },
        ]

        for project_data in projects_data:
            project, created = Project.objects.get_or_create(
                title=project_data['title'],
                defaults={
                    'creator': founder_user,
                    'short_description': project_data['short_description'],
                    'description': project_data['description'],
                    'funding_goal': project_data['funding_goal'],
                    'amount_raised': project_data['amount_raised'],
                    'deadline': project_data['deadline'],
                    'category': project_data['category'],
                    'funding_type': project_data['funding_type'],
                    'location': project_data['location'],
                    'status': project_data['status'],
                }
            )
            if created:
                self.stdout.write(f'  Created project: {project.title}')

                # Add rewards for reward-based projects
                if project.funding_type.name == 'Reward':
                    Reward.objects.create(
                        project=project,
                        title='Early Bird',
                        description='Be among the first supporters',
                        amount=Decimal('25.00'),
                    )
                    Reward.objects.create(
                        project=project,
                        title='Standard Supporter',
                        description='Support our mission with great perks',
                        amount=Decimal('50.00'),
                    )
                    Reward.objects.create(
                        project=project,
                        title='Premium Backer',
                        description='Premium rewards and recognition',
                        amount=Decimal('100.00'),
                    )

        self.stdout.write(self.style.SUCCESS(f'Projects: {Project.objects.filter(status="approved").count()} approved'))

        # Create Hero Sliders
        sliders_data = [
            {
                'title': "Empowering Africa's Next Generation of Innovators",
                'subtitle': 'Connect with visionary founders, invest through SRT tokens, or launch your own crowdfunding campaign.',
                'is_active': True,
            },
            {
                'title': 'Invest in Africa\'s Future',
                'subtitle': 'Join thousands of investors backing innovative startups across the continent.',
                'is_active': True,
            },
            {
                'title': 'Launch Your Startup Today',
                'subtitle': 'From idea to funding - we provide the platform and support you need to succeed.',
                'is_active': True,
            },
        ]

        HeroSlider.objects.all().delete()  # Clear existing sliders
        for slider_data in sliders_data:
            slider = HeroSlider.objects.create(**slider_data)
            self.stdout.write(f'  Created hero slider: {slider.title[:30]}...')

        self.stdout.write(self.style.SUCCESS(f'Hero Sliders: {HeroSlider.objects.filter(is_active=True).count()}'))

        self.stdout.write(self.style.SUCCESS('\nSample data seeding complete!'))
        self.stdout.write(f'\nDemo founder login:')
        self.stdout.write(f'  Email: founder@startupripple.com')
        self.stdout.write(f'  Password: demo12345')
