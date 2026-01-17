from django.core.management.base import BaseCommand
from django.utils.text import slugify
from apps.srt.models import TokenPackage, Venture
from decimal import Decimal


class Command(BaseCommand):
    help = 'Seed sample SRT token packages and ventures'

    def handle(self, *args, **options):
        self.stdout.write('Seeding SRT data...')

        # Create Token Packages
        packages = [
            {
                'name': 'Starter Pack',
                'tokens': 500,
                'bonus_tokens': 0,
                'price_ngn': Decimal('50000.00'),
                'price_usd': Decimal('31.25'),
                'description': 'Perfect for new partners getting started with SRT investments.',
                'is_active': True,
                'is_featured': False,
                'order': 1,
            },
            {
                'name': 'Growth Pack',
                'tokens': 1500,
                'bonus_tokens': 150,
                'price_ngn': Decimal('140000.00'),
                'price_usd': Decimal('87.50'),
                'description': 'Our most popular package with 10% bonus tokens.',
                'is_active': True,
                'is_featured': True,
                'order': 2,
            },
            {
                'name': 'Professional Pack',
                'tokens': 5000,
                'bonus_tokens': 750,
                'price_ngn': Decimal('450000.00'),
                'price_usd': Decimal('281.25'),
                'description': 'For serious investors. Get 15% bonus tokens.',
                'is_active': True,
                'is_featured': False,
                'order': 3,
            },
            {
                'name': 'Enterprise Pack',
                'tokens': 15000,
                'bonus_tokens': 3000,
                'price_ngn': Decimal('1300000.00'),
                'price_usd': Decimal('812.50'),
                'description': 'Maximum value with 20% bonus tokens. Best for institutional partners.',
                'is_active': True,
                'is_featured': False,
                'order': 4,
            },
        ]

        for pkg_data in packages:
            pkg, created = TokenPackage.objects.update_or_create(
                name=pkg_data['name'],
                defaults=pkg_data
            )
            status = 'Created' if created else 'Updated'
            self.stdout.write(f'  {status}: {pkg.name}')

        # Create Sample Ventures
        ventures = [
            {
                'title': 'AgriTech Solutions Nigeria',
                'slug': 'agritech-solutions-nigeria',
                'description': '''
                <p>AgriTech Solutions is revolutionizing farming in Nigeria through smart agriculture technology. Our platform connects smallholder farmers with markets, provides weather forecasting, and offers AI-powered crop management advice.</p>
                <h4>Key Highlights:</h4>
                <ul>
                    <li>10,000+ farmers onboarded across 5 states</li>
                    <li>Partnership with major food processors</li>
                    <li>Mobile-first platform with USSD support</li>
                    <li>Proven revenue model with 40% YoY growth</li>
                </ul>
                <p>Funds will be used to expand to 3 additional states and enhance our AI capabilities.</p>
                ''',
                'short_description': 'Smart agriculture platform connecting Nigerian farmers to markets with AI-powered insights.',
                'funding_goal': Decimal('500000.00'),
                'minimum_investment': Decimal('100.00'),
                'maximum_investment': Decimal('50000.00'),
                'expected_return_rate': Decimal('18.00'),
                'investment_duration_months': 12,
                'stage': 'growth',
                'risk_level': 'moderate',
                'industry': 'Agriculture',
                'status': 'open',
                'is_featured': True,
                'order': 1,
            },
            {
                'title': 'FinFlow Payment Gateway',
                'slug': 'finflow-payment-gateway',
                'description': '''
                <p>FinFlow is building Africa's next-generation payment infrastructure. Our API-first approach enables businesses to accept payments, send payouts, and manage their finances seamlessly.</p>
                <h4>Traction:</h4>
                <ul>
                    <li>Processing $2M+ monthly transaction volume</li>
                    <li>200+ merchants integrated</li>
                    <li>Licensed by CBN</li>
                    <li>99.9% uptime guarantee</li>
                </ul>
                <p>This round will fund expansion into Ghana and Kenya.</p>
                ''',
                'short_description': 'Next-generation payment infrastructure for African businesses.',
                'funding_goal': Decimal('1000000.00'),
                'minimum_investment': Decimal('500.00'),
                'maximum_investment': Decimal('100000.00'),
                'expected_return_rate': Decimal('25.00'),
                'investment_duration_months': 18,
                'stage': 'growth',
                'risk_level': 'moderate',
                'industry': 'Fintech',
                'status': 'open',
                'is_featured': True,
                'order': 2,
            },
            {
                'title': 'EduLearn Africa',
                'slug': 'edulearn-africa',
                'description': '''
                <p>EduLearn Africa provides affordable, quality online education to students across the continent. Our platform offers accredited courses, professional certifications, and skill development programs.</p>
                <h4>Impact:</h4>
                <ul>
                    <li>50,000+ students enrolled</li>
                    <li>Partnership with 15 universities</li>
                    <li>85% course completion rate</li>
                    <li>Featured in Forbes Africa</li>
                </ul>
                <p>Investment will fund content creation and mobile app development.</p>
                ''',
                'short_description': 'Affordable online education platform for African students.',
                'funding_goal': Decimal('300000.00'),
                'minimum_investment': Decimal('100.00'),
                'maximum_investment': Decimal('30000.00'),
                'expected_return_rate': Decimal('15.00'),
                'investment_duration_months': 12,
                'stage': 'early',
                'risk_level': 'low',
                'industry': 'Education',
                'status': 'open',
                'is_featured': True,
                'order': 3,
            },
            {
                'title': 'GreenEnergy Solar',
                'slug': 'greenenergy-solar',
                'description': '''
                <p>GreenEnergy Solar is bringing clean, affordable solar power to Nigerian homes and businesses. Our pay-as-you-go model makes solar accessible to everyone.</p>
                <h4>Metrics:</h4>
                <ul>
                    <li>5,000+ installations completed</li>
                    <li>Carbon offset: 10,000 tons annually</li>
                    <li>95% customer retention rate</li>
                    <li>Award-winning PAYG technology</li>
                </ul>
                <p>Seeking funds to scale manufacturing and expand distribution network.</p>
                ''',
                'short_description': 'Pay-as-you-go solar solutions for Nigerian homes and businesses.',
                'funding_goal': Decimal('750000.00'),
                'minimum_investment': Decimal('200.00'),
                'maximum_investment': Decimal('75000.00'),
                'expected_return_rate': Decimal('20.00'),
                'investment_duration_months': 24,
                'stage': 'expansion',
                'risk_level': 'moderate',
                'industry': 'Clean Energy',
                'status': 'open',
                'is_featured': False,
                'order': 4,
            },
            {
                'title': 'HealthConnect Telemedicine',
                'slug': 'healthconnect-telemedicine',
                'description': '''
                <p>HealthConnect is making healthcare accessible through telemedicine. Our platform connects patients with licensed doctors for virtual consultations, prescriptions, and follow-ups.</p>
                <h4>Growth:</h4>
                <ul>
                    <li>100,000+ consultations completed</li>
                    <li>500+ doctors on platform</li>
                    <li>24/7 availability</li>
                    <li>Insurance partnerships</li>
                </ul>
                <p>Funds will support AI diagnostics integration and rural expansion.</p>
                ''',
                'short_description': 'Telemedicine platform connecting patients with doctors across Africa.',
                'funding_goal': Decimal('600000.00'),
                'minimum_investment': Decimal('150.00'),
                'maximum_investment': Decimal('60000.00'),
                'expected_return_rate': Decimal('22.00'),
                'investment_duration_months': 18,
                'stage': 'growth',
                'risk_level': 'moderate',
                'industry': 'Healthcare',
                'status': 'open',
                'is_featured': False,
                'order': 5,
            },
            {
                'title': 'LogiMove Delivery',
                'slug': 'logimove-delivery',
                'description': '''
                <p>LogiMove is transforming last-mile delivery in Lagos and Abuja. Our technology-driven logistics platform ensures fast, reliable, and affordable deliveries for e-commerce businesses.</p>
                <h4>Performance:</h4>
                <ul>
                    <li>50,000+ deliveries monthly</li>
                    <li>98% on-time delivery rate</li>
                    <li>Major e-commerce partnerships</li>
                    <li>Profitable unit economics</li>
                </ul>
                <p>Investment to fund fleet expansion and technology upgrades.</p>
                ''',
                'short_description': 'Technology-driven last-mile delivery for Nigerian e-commerce.',
                'funding_goal': Decimal('400000.00'),
                'minimum_investment': Decimal('100.00'),
                'maximum_investment': Decimal('40000.00'),
                'expected_return_rate': Decimal('16.00'),
                'investment_duration_months': 12,
                'stage': 'growth',
                'risk_level': 'low',
                'industry': 'Logistics',
                'status': 'open',
                'is_featured': False,
                'order': 6,
            },
        ]

        for venture_data in ventures:
            venture, created = Venture.objects.update_or_create(
                slug=venture_data['slug'],
                defaults=venture_data
            )
            status = 'Created' if created else 'Updated'
            self.stdout.write(f'  {status}: {venture.title}')

        self.stdout.write(self.style.SUCCESS('\nSRT data seeding completed!'))
        self.stdout.write(f'  Token Packages: {TokenPackage.objects.count()}')
        self.stdout.write(f'  Ventures: {Venture.objects.count()}')
