"""
Management command to populate initial content for legal pages.
Run: python manage.py populate_legal_pages
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.cms.models import LegalPage


class Command(BaseCommand):
    help = 'Populates initial content for Terms & Conditions and Investment Risk Disclosure pages'

    def handle(self, *args, **options):
        self.stdout.write('Creating legal pages...')

        # Terms & Conditions
        terms_content = """
<h2>1. Introduction and Acceptance</h2>
<p>Welcome to StartUpRipple ("Platform", "we", "us", or "our"). These Terms and Conditions ("Terms") govern your access to and use of our website, mobile applications, and services (collectively, the "Services").</p>
<p>By accessing or using our Services, you acknowledge that you have read, understood, and agree to be bound by these Terms. If you do not agree to these Terms, please do not access or use our Services.</p>
<p><strong>Important:</strong> These Terms contain provisions that limit our liability and require you to resolve disputes through arbitration on an individual basis. Please read these Terms carefully.</p>

<h2>2. Eligibility and Account Registration</h2>
<h3>2.1 Eligibility Requirements</h3>
<p>To use our Services, you must:</p>
<ul>
<li>Be at least 18 years of age or the age of legal majority in your jurisdiction</li>
<li>Have the legal capacity to enter into binding contracts</li>
<li>Not be prohibited from using the Services under applicable laws</li>
<li>Provide accurate and complete registration information</li>
<li>Maintain the security of your account credentials</li>
</ul>

<h3>2.2 Account Types</h3>
<p>StartUpRipple offers the following account types:</p>
<ul>
<li><strong>Founder Account:</strong> For entrepreneurs seeking funding for their projects</li>
<li><strong>Investor Account:</strong> For individuals making equity investments in projects</li>
<li><strong>Donor Account:</strong> For individuals making donations or pledges to projects</li>
<li><strong>SRT Partner Account:</strong> For token-based investment in vetted ventures</li>
</ul>

<h3>2.3 Account Security</h3>
<p>You are responsible for:</p>
<ul>
<li>Maintaining the confidentiality of your login credentials</li>
<li>All activities that occur under your account</li>
<li>Immediately notifying us of any unauthorized use of your account</li>
<li>Ensuring your contact information remains current and accurate</li>
</ul>

<h2>3. StartUp Ripple Tokens (SRT)</h2>
<h3>3.1 Token Overview</h3>
<p>SRT Tokens are digital units used within our platform to facilitate investments in vetted startup ventures. Key features include:</p>
<ul>
<li><strong>Token Value:</strong> 1 SRT = ₦2,000 (Nigerian Naira)</li>
<li><strong>Purchase Limits:</strong> Maximum of 200 SRT tokens per partner per month</li>
<li><strong>Usage:</strong> Tokens can be used to invest in approved ventures on the platform</li>
</ul>

<h3>3.2 Token Purchases</h3>
<p>When purchasing SRT tokens:</p>
<ul>
<li>All purchases are processed through our secure payment gateway (Paystack)</li>
<li>Tokens are credited to your account upon successful payment confirmation</li>
<li>Monthly purchase limits are calculated based on calendar months</li>
<li>Token purchases are final and non-refundable except as provided in our Refund Policy</li>
</ul>

<h3>3.3 Token Redemption and Withdrawals</h3>
<p>SRT token holders may request withdrawals subject to:</p>
<ul>
<li>Minimum withdrawal requirements as specified on the platform</li>
<li>Processing times of 5-7 business days for standard withdrawals</li>
<li>Verification of bank account details</li>
<li>Applicable fees as disclosed at the time of withdrawal request</li>
</ul>

<h2>4. Investment Terms</h2>
<h3>4.1 Investment Process</h3>
<p>When making investments through the Platform:</p>
<ul>
<li>Review all project information and disclosure documents carefully</li>
<li>Understand that all investments carry risk of partial or total loss</li>
<li>Acknowledge that past performance does not guarantee future results</li>
<li>Confirm that you can afford to lose your entire investment</li>
</ul>

<h3>4.2 Investment Modifications</h3>
<p>Investors may modify or cancel pending investments:</p>
<ul>
<li>Modifications are subject to availability and project terms</li>
<li>Cancellation requests must be made before investment maturity</li>
<li>Early withdrawal may result in reduced returns or penalties</li>
</ul>

<h3>4.3 Returns and Payouts</h3>
<p>Investment returns are:</p>
<ul>
<li>Subject to the success and performance of the underlying venture</li>
<li>Not guaranteed and may be less than the original investment</li>
<li>Paid according to the schedule specified for each investment term</li>
<li>Subject to applicable taxes and regulatory requirements</li>
</ul>

<h2>5. Project Submission and Funding</h2>
<h3>5.1 For Founders</h3>
<p>Founders submitting projects must:</p>
<ul>
<li>Provide accurate and complete information about their project</li>
<li>Disclose all material risks and challenges</li>
<li>Use funds received solely for stated project purposes</li>
<li>Provide regular updates to investors and donors</li>
<li>Comply with all applicable laws and regulations</li>
</ul>

<h3>5.2 Project Review</h3>
<p>All projects undergo review by StartUpRipple, which may include:</p>
<ul>
<li>Verification of founder identity and business credentials</li>
<li>Assessment of project viability and risk factors</li>
<li>Review of financial projections and funding requirements</li>
<li>Compliance with platform guidelines and legal requirements</li>
</ul>

<h2>6. Fees and Payments</h2>
<h3>6.1 Platform Fees</h3>
<p>StartUpRipple may charge fees for:</p>
<ul>
<li>Registration (varies by account type)</li>
<li>Transaction processing</li>
<li>Withdrawal processing</li>
<li>Premium features and services</li>
</ul>
<p>All applicable fees will be disclosed before any transaction.</p>

<h3>6.2 Payment Processing</h3>
<p>Payments are processed through secure third-party payment providers. By using our Services, you agree to the terms and conditions of these payment processors.</p>

<h2>7. User Conduct</h2>
<p>When using our Services, you agree NOT to:</p>
<ul>
<li>Provide false, misleading, or fraudulent information</li>
<li>Engage in money laundering or other illegal financial activities</li>
<li>Manipulate or interfere with the Platform's operation</li>
<li>Harass, abuse, or harm other users</li>
<li>Violate any applicable laws or regulations</li>
<li>Attempt to gain unauthorized access to the Platform or other users' accounts</li>
<li>Use the Platform for any purpose other than its intended use</li>
</ul>

<h2>8. Intellectual Property</h2>
<p>All content on the Platform, including text, graphics, logos, and software, is the property of StartUpRipple or its licensors and is protected by intellectual property laws. You may not reproduce, distribute, or create derivative works without our express written permission.</p>

<h2>9. Privacy and Data Protection</h2>
<p>Your use of our Services is also governed by our Privacy Policy, which describes how we collect, use, and protect your personal information. By using our Services, you consent to our data practices as described in the Privacy Policy.</p>

<h2>10. Disclaimers</h2>
<blockquote>
<p><strong>THE SERVICES ARE PROVIDED "AS IS" AND "AS AVAILABLE" WITHOUT WARRANTIES OF ANY KIND, EXPRESS OR IMPLIED.</strong></p>
</blockquote>
<p>We do not warrant that:</p>
<ul>
<li>The Services will be uninterrupted or error-free</li>
<li>Any investment will generate returns or be profitable</li>
<li>Project information provided by founders is accurate or complete</li>
<li>The Platform will meet your specific requirements</li>
</ul>

<h2>11. Limitation of Liability</h2>
<p>TO THE MAXIMUM EXTENT PERMITTED BY LAW:</p>
<ul>
<li>StartUpRipple shall not be liable for any indirect, incidental, special, consequential, or punitive damages</li>
<li>Our total liability shall not exceed the fees paid by you in the 12 months preceding the claim</li>
<li>We are not responsible for investment losses or project failures</li>
</ul>

<h2>12. Indemnification</h2>
<p>You agree to indemnify and hold harmless StartUpRipple, its officers, directors, employees, and agents from any claims, damages, or expenses arising from your use of the Services or violation of these Terms.</p>

<h2>13. Modifications to Terms</h2>
<p>We may modify these Terms at any time. Material changes will be notified via email or platform notification. Continued use of the Services after changes constitutes acceptance of the modified Terms.</p>

<h2>14. Termination</h2>
<p>We may suspend or terminate your account if you:</p>
<ul>
<li>Violate these Terms</li>
<li>Engage in fraudulent or illegal activity</li>
<li>Provide false information</li>
<li>Fail to comply with applicable laws</li>
</ul>
<p>Upon termination, you remain responsible for all obligations incurred prior to termination.</p>

<h2>15. Governing Law and Dispute Resolution</h2>
<p>These Terms are governed by the laws of the Federal Republic of Nigeria. Any disputes shall be resolved through binding arbitration in Lagos, Nigeria, except where prohibited by law.</p>

<h2>16. Contact Information</h2>
<p>For questions about these Terms, please contact us:</p>
<ul>
<li><strong>Email:</strong> legal@startupripple.com</li>
<li><strong>Address:</strong> StartUpRipple Ltd., Lagos, Nigeria</li>
</ul>
"""

        terms, created = LegalPage.objects.update_or_create(
            page_type='terms',
            defaults={
                'title': 'Terms & Conditions',
                'subtitle': 'Please read these terms carefully before using our platform and services.',
                'content': terms_content,
                'effective_date': timezone.now().date(),
                'version': '1.0',
                'is_published': True,
                'show_table_of_contents': True,
            }
        )
        status = 'Created' if created else 'Updated'
        self.stdout.write(self.style.SUCCESS(f'{status}: Terms & Conditions'))

        # Investment Risk Disclosure
        risk_content = """
<h2>1. Introduction</h2>
<p>This Investment Risk Disclosure ("Disclosure") provides important information about the risks associated with investing through the StartUpRipple platform. All prospective and current investors must read and understand this document before making any investment decisions.</p>

<blockquote>
<p><strong>IMPORTANT:</strong> Investing in startups and early-stage ventures involves substantial risk, including the risk of losing your entire investment. Only invest money that you can afford to lose completely.</p>
</blockquote>

<h2>2. General Investment Risks</h2>
<h3>2.1 Risk of Loss</h3>
<p>Investments in startups and early-stage companies carry a high degree of risk. Key risks include:</p>
<ul>
<li><strong>Total Loss of Capital:</strong> You may lose 100% of your investment</li>
<li><strong>No Guaranteed Returns:</strong> Past performance does not guarantee future results</li>
<li><strong>Long-Term Commitment:</strong> Your capital may be locked for extended periods</li>
<li><strong>Illiquidity:</strong> You may not be able to sell or transfer your investment easily</li>
</ul>

<h3>2.2 Business Risks</h3>
<p>Startup ventures face numerous business challenges:</p>
<ul>
<li>High failure rate of startup businesses (historically 70-90%)</li>
<li>Competition from established companies and other startups</li>
<li>Difficulty achieving product-market fit</li>
<li>Challenges in scaling operations</li>
<li>Dependence on key personnel</li>
<li>Limited operating history and track record</li>
</ul>

<h3>2.3 Market Risks</h3>
<ul>
<li>Economic downturns affecting business performance</li>
<li>Changes in market conditions and consumer preferences</li>
<li>Currency fluctuations affecting returns</li>
<li>Interest rate changes impacting valuations</li>
<li>Sector-specific market disruptions</li>
</ul>

<h2>3. Platform-Specific Risks</h2>
<h3>3.1 SRT Token Risks</h3>
<p>Investing through SRT tokens involves specific risks:</p>
<ul>
<li><strong>Token Value:</strong> The value of SRT tokens is fixed at ₦2,000 but returns are not guaranteed</li>
<li><strong>Platform Dependency:</strong> Tokens can only be used within the StartUpRipple ecosystem</li>
<li><strong>Regulatory Risk:</strong> Changes in regulations may affect token usage or value</li>
<li><strong>Technical Risk:</strong> Platform technical issues may affect access or transactions</li>
</ul>

<h3>3.2 Venture Selection Risks</h3>
<p>While StartUpRipple reviews and vets projects, investors should understand:</p>
<ul>
<li>Due diligence cannot eliminate all risks</li>
<li>Project information is primarily provided by founders</li>
<li>Business projections may not materialize as expected</li>
<li>Verification processes have limitations</li>
</ul>

<h3>3.3 Concentration Risk</h3>
<p>Investing a significant portion of your capital in a single venture or sector increases risk. Diversification across multiple investments may help reduce, but does not eliminate, risk.</p>

<h2>4. Financial Risks</h2>
<h3>4.1 Return Expectations</h3>
<p>Regarding investment returns:</p>
<ul>
<li>Expected returns shown are projections, not guarantees</li>
<li>Actual returns may be significantly lower than projected</li>
<li>Returns depend on venture performance and market conditions</li>
<li>Payment of returns is subject to venture's ability to pay</li>
</ul>

<h3>4.2 Withdrawal Risks</h3>
<ul>
<li>Early withdrawal may result in reduced or no returns</li>
<li>Withdrawal processing takes 5-7 business days</li>
<li>Withdrawal requests are subject to available funds</li>
<li>In extreme cases, withdrawals may be delayed or limited</li>
</ul>

<h3>4.3 Currency and Inflation Risks</h3>
<ul>
<li>Investments and returns are denominated in Nigerian Naira (₦)</li>
<li>Currency depreciation may affect real value of returns</li>
<li>Inflation may erode purchasing power of returns</li>
</ul>

<h2>5. Operational and Technical Risks</h2>
<h3>5.1 Platform Risks</h3>
<ul>
<li>Technical failures or cybersecurity breaches</li>
<li>Service interruptions affecting access to investments</li>
<li>Changes to platform features or policies</li>
<li>Potential platform closure or business failure</li>
</ul>

<h3>5.2 Third-Party Risks</h3>
<ul>
<li>Payment processor failures or issues</li>
<li>Banking system disruptions</li>
<li>Third-party service provider risks</li>
</ul>

<h2>6. Legal and Regulatory Risks</h2>
<h3>6.1 Regulatory Environment</h3>
<ul>
<li>Changes in investment regulations affecting operations</li>
<li>Tax law changes affecting returns</li>
<li>New compliance requirements</li>
<li>Cross-border transaction restrictions</li>
</ul>

<h3>6.2 Legal Recourse</h3>
<ul>
<li>Limited legal recourse in case of disputes</li>
<li>Arbitration requirements for dispute resolution</li>
<li>Costs and complexities of legal action</li>
</ul>

<h2>7. Fraud and Misrepresentation Risks</h2>
<p>While StartUpRipple takes measures to prevent fraud:</p>
<ul>
<li>Founders may provide inaccurate or misleading information</li>
<li>Projects may fail to deliver on promises</li>
<li>Funds may not be used as disclosed</li>
<li>Detection of fraud may occur after investment is made</li>
</ul>

<h2>8. Risk Mitigation Strategies</h2>
<p>Investors are encouraged to:</p>
<ul>
<li><strong>Diversify:</strong> Spread investments across multiple ventures and sectors</li>
<li><strong>Research:</strong> Conduct your own due diligence on projects</li>
<li><strong>Invest Wisely:</strong> Only invest funds you can afford to lose</li>
<li><strong>Understand:</strong> Read all project documentation thoroughly</li>
<li><strong>Ask Questions:</strong> Seek clarification on anything unclear</li>
<li><strong>Stay Informed:</strong> Monitor your investments and project updates</li>
<li><strong>Seek Advice:</strong> Consult with financial advisors if needed</li>
</ul>

<h2>9. Investment Suitability</h2>
<h3>9.1 Who Should Consider Investing</h3>
<p>Our platform may be suitable for investors who:</p>
<ul>
<li>Have a high tolerance for risk</li>
<li>Can afford to lose their entire investment</li>
<li>Understand the illiquid nature of startup investments</li>
<li>Have a long-term investment horizon</li>
<li>Are comfortable with the uncertainties involved</li>
</ul>

<h3>9.2 Who Should Not Invest</h3>
<p>Our platform may NOT be suitable for investors who:</p>
<ul>
<li>Cannot afford to lose any of their investment capital</li>
<li>Need guaranteed returns</li>
<li>Require immediate access to their funds</li>
<li>Are seeking short-term gains</li>
<li>Are not comfortable with high-risk investments</li>
</ul>

<h2>10. No Investment Advice</h2>
<blockquote>
<p>StartUpRipple does NOT provide investment, legal, or tax advice. The information provided on our platform is for informational purposes only and should not be construed as a recommendation to invest in any particular project or venture.</p>
</blockquote>
<p>You should consult with qualified professionals before making investment decisions based on your individual circumstances, objectives, and risk tolerance.</p>

<h2>11. Investor Acknowledgments</h2>
<p>By investing through StartUpRipple, you acknowledge and confirm that:</p>
<ul>
<li>You have read and understood this Risk Disclosure document</li>
<li>You understand the risks involved in startup investments</li>
<li>You are investing with funds you can afford to lose</li>
<li>You have conducted your own due diligence</li>
<li>You are making your own independent investment decisions</li>
<li>You will not hold StartUpRipple responsible for investment losses</li>
</ul>

<h2>12. Updates to This Disclosure</h2>
<p>This Risk Disclosure may be updated periodically to reflect changes in risks, regulations, or platform operations. We encourage you to review this document regularly. Material changes will be communicated through platform notifications or email.</p>

<h2>13. Questions and Concerns</h2>
<p>If you have questions about the risks associated with investing on our platform, please contact us:</p>
<ul>
<li><strong>Email:</strong> investments@startupripple.com</li>
<li><strong>Support:</strong> support@startupripple.com</li>
</ul>

<p><strong>Remember:</strong> Only invest what you can afford to lose. If you're uncertain about your investment decisions, please consult with a qualified financial advisor.</p>
"""

        risk, created = LegalPage.objects.update_or_create(
            page_type='investment_risk',
            defaults={
                'title': 'Investment Risk Disclosure',
                'subtitle': 'Important information about the risks of investing through our platform.',
                'content': risk_content,
                'effective_date': timezone.now().date(),
                'version': '1.0',
                'is_published': True,
                'show_table_of_contents': True,
            }
        )
        status = 'Created' if created else 'Updated'
        self.stdout.write(self.style.SUCCESS(f'{status}: Investment Risk Disclosure'))

        # Privacy Policy
        privacy_content = """
<h2>1. Introduction</h2>
<p>StartUpRipple ("we", "us", or "our") is committed to protecting your privacy. This Privacy Policy explains how we collect, use, disclose, and safeguard your personal information when you use our platform and services.</p>

<h2>2. Information We Collect</h2>
<h3>2.1 Personal Information</h3>
<p>We may collect the following personal information:</p>
<ul>
<li>Name, email address, phone number</li>
<li>Date of birth and government-issued ID</li>
<li>Residential and business addresses</li>
<li>Bank account and payment information</li>
<li>Employment and financial information</li>
</ul>

<h3>2.2 Automatically Collected Information</h3>
<ul>
<li>IP address and device information</li>
<li>Browser type and operating system</li>
<li>Usage patterns and preferences</li>
<li>Cookies and similar technologies</li>
</ul>

<h2>3. How We Use Your Information</h2>
<p>We use your information to:</p>
<ul>
<li>Provide and maintain our services</li>
<li>Process transactions and investments</li>
<li>Verify your identity and prevent fraud</li>
<li>Communicate with you about your account</li>
<li>Comply with legal and regulatory requirements</li>
<li>Improve our platform and services</li>
</ul>

<h2>4. Information Sharing</h2>
<p>We may share your information with:</p>
<ul>
<li>Service providers who assist our operations</li>
<li>Payment processors for transactions</li>
<li>Regulatory authorities as required by law</li>
<li>Business partners with your consent</li>
</ul>

<h2>5. Data Security</h2>
<p>We implement industry-standard security measures including:</p>
<ul>
<li>Encryption of sensitive data</li>
<li>Secure server infrastructure</li>
<li>Regular security assessments</li>
<li>Employee training and access controls</li>
</ul>

<h2>6. Your Rights</h2>
<p>You have the right to:</p>
<ul>
<li>Access your personal information</li>
<li>Correct inaccurate data</li>
<li>Request deletion of your data</li>
<li>Opt-out of marketing communications</li>
<li>Export your data in a portable format</li>
</ul>

<h2>7. Contact Us</h2>
<p>For privacy-related inquiries, contact us at:</p>
<ul>
<li><strong>Email:</strong> privacy@startupripple.com</li>
<li><strong>Address:</strong> StartUpRipple Ltd., Lagos, Nigeria</li>
</ul>
"""

        privacy, created = LegalPage.objects.update_or_create(
            page_type='privacy',
            defaults={
                'title': 'Privacy Policy',
                'subtitle': 'How we collect, use, and protect your personal information.',
                'content': privacy_content,
                'effective_date': timezone.now().date(),
                'version': '1.0',
                'is_published': True,
                'show_table_of_contents': True,
            }
        )
        status = 'Created' if created else 'Updated'
        self.stdout.write(self.style.SUCCESS(f'{status}: Privacy Policy'))

        self.stdout.write(self.style.SUCCESS('\nAll legal pages created successfully!'))
        self.stdout.write('You can now edit these pages from the admin panel.')
