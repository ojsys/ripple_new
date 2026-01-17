from django.core.management.base import BaseCommand
from apps.cms.models import AboutPage, TeamMember


class Command(BaseCommand):
    help = 'Populate About Page content and Team Members'

    def handle(self, *args, **options):
        self.stdout.write('Populating About Page content...')

        # Create or update AboutPage
        about, created = AboutPage.objects.update_or_create(
            pk=1,
            defaults={
                'title': 'About Us',
                'content': '''
                    <p class="lead">StartUpRipples is a platform and ecosystem designed to empower early-stage founders
                    with the tools, knowledge, visibility, and capital they need to build world-changing startups from the ground up.</p>

                    <p>We believe that great ideas can come from anywhere, and we're committed to ensuring that geography,
                    background, or access to traditional networks doesn't determine a founder's success. Our platform connects
                    innovative African entrepreneurs with the resources, mentorship, and funding they need to transform their
                    visions into reality.</p>

                    <p>Through our unique combination of crowdfunding, token-based investments (SRT), and accelerator programs,
                    we're creating new pathways for startup success across the continent.</p>
                ''',
                'mission': '''To democratize startup access to funding, knowledge, and community by supporting high-potential
                founders at the earliest stages—especially those outside traditional tech hubs. We're building bridges between
                visionary founders and the resources they need to succeed, one ripple at a time.''',
                'vision': '''To become the leading launchpad for Africa's next generation of founders by transforming ideas
                into investable ventures, one ripple at a time. We envision an Africa where every promising entrepreneur has
                the opportunity to build, scale, and succeed.''',
                'core_values': '''
                    <div class="values-grid">
                        <div class="value-item">
                            <div class="value-icon">
                                <i class="fas fa-users"></i>
                            </div>
                            <div class="value-content">
                                <h4>Founder-First</h4>
                                <p>We prioritize venture builders and creators. Every decision we make is guided by what's best for the founders we serve.</p>
                            </div>
                        </div>
                        <div class="value-item">
                            <div class="value-icon">
                                <i class="fas fa-lightbulb"></i>
                            </div>
                            <div class="value-content">
                                <h4>Clarity Over Complexity</h4>
                                <p>We teach fundamentals rather than unnecessary complexities. Simple, actionable guidance beats complicated theories.</p>
                            </div>
                        </div>
                        <div class="value-item">
                            <div class="value-icon">
                                <i class="fas fa-hand-holding-heart"></i>
                            </div>
                            <div class="value-content">
                                <h4>Skin in the Game</h4>
                                <p>We support those actively building. We invest our time, resources, and reputation alongside our founders.</p>
                            </div>
                        </div>
                        <div class="value-item">
                            <div class="value-icon">
                                <i class="fas fa-rocket"></i>
                            </div>
                            <div class="value-content">
                                <h4>Progress, Not Perfection</h4>
                                <p>We value momentum over perfectionism. Taking action and learning from it beats endless planning.</p>
                            </div>
                        </div>
                        <div class="value-item">
                            <div class="value-icon">
                                <i class="fas fa-bolt"></i>
                            </div>
                            <div class="value-content">
                                <h4>Courage to Challenge</h4>
                                <p>We encourage ambitious thinking and smart execution. Big problems require bold solutions.</p>
                            </div>
                        </div>
                    </div>
                ''',
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS('Created new AboutPage'))
        else:
            self.stdout.write(self.style.SUCCESS('Updated existing AboutPage'))

        # Create Team Members
        team_members_data = [
            {
                'name': 'Fwangmun Oscar Danladi',
                'position': 'Co-Founder & Managing Partner',
                'bio': '''A grassroots organizer with a background in sociology and theology, Oscar is deeply focused on
                youth development and social justice in Nigeria. His experience in community organizing and passion for
                empowering young people drives the vision and strategic direction of StartUpRipples. He believes in the
                transformative power of entrepreneurship to create lasting social change.''',
                'order': 1,
            },
            {
                'name': 'Abel Eleojo Ochika',
                'position': 'Co-Founder & Platform Operations',
                'bio': '''A youth leader specializing in community development, social justice, and climate action,
                Abel brings strong communication expertise to the team. He oversees platform operations and ensures
                that StartUpRipples remains true to its mission of serving founders across Africa. His background in
                advocacy and community building helps create an inclusive platform for all.''',
                'order': 2,
            },
            {
                'name': 'Jonah Onah',
                'position': 'Co-Founder & Program/Venture Lead',
                'bio': '''A software engineer with 7+ years of experience building inclusive digital solutions for
                agriculture and emerging markets, Jonah leads our venture programs and technical development. His
                hands-on experience building startups from the ground up gives him unique insight into what founders
                need to succeed. He's passionate about using technology to solve real problems.''',
                'order': 3,
            },
        ]

        for member_data in team_members_data:
            member, created = TeamMember.objects.update_or_create(
                name=member_data['name'],
                defaults={
                    'position': member_data['position'],
                    'bio': member_data['bio'],
                    'order': member_data['order'],
                    'is_active': True,
                    'is_visible': True,
                }
            )

            # Add team member to about page
            about.team_members.add(member)

            if created:
                self.stdout.write(self.style.SUCCESS(f'Created team member: {member.name}'))
            else:
                self.stdout.write(self.style.SUCCESS(f'Updated team member: {member.name}'))

        self.stdout.write(self.style.SUCCESS('Successfully populated About Page content!'))
