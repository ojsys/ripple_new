# Generated data migration for seeding Legal Pages

from django.db import migrations


def create_legal_pages(apps, schema_editor):
    """Create initial legal pages."""
    LegalPage = apps.get_model('cms', 'LegalPage')

    # Terms & Conditions
    if not LegalPage.objects.filter(page_type='terms').exists():
        LegalPage.objects.create(
            page_type='terms',
            title='Terms & Conditions',
            subtitle='Please read these terms carefully before using our platform',
            content='''
<h2>1. Acceptance of Terms</h2>
<p>By accessing and using StartUpRipple ("the Platform"), you accept and agree to be bound by the terms and provisions of this agreement. If you do not agree to abide by these terms, please do not use this service.</p>

<h2>2. Description of Service</h2>
<p>StartUpRipple is a crowdfunding and investment platform that connects entrepreneurs (Founders) with potential investors and donors. The Platform facilitates:</p>
<ul>
    <li>Equity-based investments in startups</li>
    <li>Donation-based crowdfunding campaigns</li>
    <li>SRT Partner investment programs</li>
    <li>Incubator and accelerator program applications</li>
</ul>

<h2>3. User Accounts</h2>
<p>To access certain features of the Platform, you must register for an account. You agree to:</p>
<ul>
    <li>Provide accurate, current, and complete information during registration</li>
    <li>Maintain and promptly update your account information</li>
    <li>Maintain the security of your password and accept all risks of unauthorized access</li>
    <li>Notify us immediately if you discover any unauthorized use of your account</li>
</ul>

<h2>4. User Types and Responsibilities</h2>
<h3>4.1 Founders</h3>
<p>Founders who list projects on the Platform agree to:</p>
<ul>
    <li>Provide truthful and accurate information about their projects</li>
    <li>Use funds raised exclusively for the stated project purposes</li>
    <li>Provide regular updates to investors and backers</li>
    <li>Comply with all applicable laws and regulations</li>
</ul>

<h3>4.2 Investors</h3>
<p>Investors using the Platform acknowledge that:</p>
<ul>
    <li>Investments in startups carry significant risk, including total loss of investment</li>
    <li>Past performance does not guarantee future results</li>
    <li>They have read and understood the Investment Risk Disclosure</li>
</ul>

<h3>4.3 Donors</h3>
<p>Donors understand that contributions are generally non-refundable and are made to support projects without expectation of financial return.</p>

<h2>5. Fees and Payments</h2>
<p>The Platform charges fees for certain services, including:</p>
<ul>
    <li>Registration fees for different account types</li>
    <li>Transaction fees on successful funding</li>
    <li>Payment processing fees</li>
</ul>
<p>All fees are clearly disclosed before any transaction is completed.</p>

<h2>6. Intellectual Property</h2>
<p>The Platform and its original content, features, and functionality are owned by StartUpRipple and are protected by international copyright, trademark, and other intellectual property laws.</p>

<h2>7. Limitation of Liability</h2>
<p>StartUpRipple shall not be liable for any indirect, incidental, special, consequential, or punitive damages resulting from your use of or inability to use the Platform.</p>

<h2>8. Changes to Terms</h2>
<p>We reserve the right to modify these terms at any time. We will notify users of any material changes via email or through the Platform. Continued use of the Platform after changes constitutes acceptance of the new terms.</p>

<h2>9. Contact Information</h2>
<p>For questions about these Terms & Conditions, please contact us at legal@startupripple.com</p>
            ''',
            version='1.0',
            is_published=True,
            show_table_of_contents=True
        )

    # Investment Risk Disclosure
    if not LegalPage.objects.filter(page_type='investment_risk').exists():
        LegalPage.objects.create(
            page_type='investment_risk',
            title='Investment Risk Disclosure',
            subtitle='Important information about the risks of investing in startups',
            content='''
<h2>Important Notice</h2>
<p><strong>Investing in startups and early-stage companies involves significant risks, including the risk of losing your entire investment.</strong> Please read this disclosure carefully before making any investment decisions.</p>

<h2>1. Risk of Loss</h2>
<p>Investments in startups are speculative and involve a high degree of risk. Unlike traditional investments, startup investments:</p>
<ul>
    <li>May result in total loss of your invested capital</li>
    <li>Are highly illiquid and may not be easily sold or transferred</li>
    <li>May not generate any returns for extended periods, if ever</li>
    <li>Are not protected by any government insurance or guarantee programs</li>
</ul>

<h2>2. Startup Failure Rates</h2>
<p>Statistics show that a significant percentage of startups fail within their first few years of operation. Factors contributing to failure include:</p>
<ul>
    <li>Insufficient market demand for products or services</li>
    <li>Cash flow problems and inability to secure additional funding</li>
    <li>Strong competition from established companies</li>
    <li>Management and operational challenges</li>
    <li>Economic downturns and market conditions</li>
</ul>

<h2>3. Lack of Liquidity</h2>
<p>Startup investments are typically highly illiquid. You should be prepared to hold your investment for an extended period (often 5-10 years or more) and may never have an opportunity to sell your shares.</p>

<h2>4. Dilution</h2>
<p>Your ownership stake may be diluted in future funding rounds. As companies raise additional capital, your percentage ownership will decrease unless you participate in subsequent rounds.</p>

<h2>5. Limited Information</h2>
<p>Startups may have limited operating history and financial data. Unlike public companies, they are not required to disclose detailed financial information, making it difficult to assess their true value and prospects.</p>

<h2>6. No Guaranteed Returns</h2>
<p>There is no guarantee that any investment will generate returns. Projected returns and financial forecasts are speculative and may not materialize.</p>

<h2>7. Diversification</h2>
<p>We strongly recommend diversifying your investment portfolio. Do not invest more than you can afford to lose, and consider startup investments as only a small portion of your overall investment strategy.</p>

<h2>8. Professional Advice</h2>
<p>Before making any investment, we recommend consulting with qualified financial, legal, and tax advisors who can assess your personal situation and risk tolerance.</p>

<h2>9. Your Acknowledgment</h2>
<p>By investing through StartUpRipple, you acknowledge that you have:</p>
<ul>
    <li>Read and understood this Risk Disclosure</li>
    <li>Conducted your own due diligence on any investment</li>
    <li>Made your investment decision independently</li>
    <li>Accepted the risks associated with startup investing</li>
</ul>
            ''',
            version='1.0',
            is_published=True,
            show_table_of_contents=True
        )

    # Privacy Policy
    if not LegalPage.objects.filter(page_type='privacy').exists():
        LegalPage.objects.create(
            page_type='privacy',
            title='Privacy Policy',
            subtitle='How we collect, use, and protect your personal information',
            content='''
<h2>1. Introduction</h2>
<p>StartUpRipple ("we," "our," or "us") is committed to protecting your privacy. This Privacy Policy explains how we collect, use, disclose, and safeguard your information when you use our platform.</p>

<h2>2. Information We Collect</h2>
<h3>2.1 Personal Information</h3>
<p>We may collect personal information that you voluntarily provide, including:</p>
<ul>
    <li>Name, email address, and phone number</li>
    <li>Billing and payment information</li>
    <li>Identity verification documents</li>
    <li>Professional and business information</li>
    <li>Investment preferences and history</li>
</ul>

<h3>2.2 Automatically Collected Information</h3>
<p>When you access our platform, we automatically collect:</p>
<ul>
    <li>Device and browser information</li>
    <li>IP address and location data</li>
    <li>Usage patterns and preferences</li>
    <li>Cookies and similar tracking technologies</li>
</ul>

<h2>3. How We Use Your Information</h2>
<p>We use the collected information to:</p>
<ul>
    <li>Provide, operate, and maintain our platform</li>
    <li>Process transactions and send related information</li>
    <li>Verify your identity and prevent fraud</li>
    <li>Send promotional communications (with your consent)</li>
    <li>Respond to your comments, questions, and requests</li>
    <li>Comply with legal obligations</li>
</ul>

<h2>4. Information Sharing</h2>
<p>We may share your information with:</p>
<ul>
    <li>Service providers who assist in our operations</li>
    <li>Project founders (for investors/donors)</li>
    <li>Regulatory authorities when required by law</li>
    <li>Business partners with your consent</li>
</ul>
<p>We do not sell your personal information to third parties.</p>

<h2>5. Data Security</h2>
<p>We implement appropriate technical and organizational measures to protect your personal information, including:</p>
<ul>
    <li>Encryption of sensitive data</li>
    <li>Secure server infrastructure</li>
    <li>Regular security assessments</li>
    <li>Access controls and authentication</li>
</ul>

<h2>6. Your Rights</h2>
<p>You have the right to:</p>
<ul>
    <li>Access your personal information</li>
    <li>Correct inaccurate data</li>
    <li>Request deletion of your data</li>
    <li>Opt-out of marketing communications</li>
    <li>Data portability</li>
</ul>

<h2>7. Cookies</h2>
<p>We use cookies and similar technologies to enhance your experience. You can control cookie preferences through your browser settings.</p>

<h2>8. Children's Privacy</h2>
<p>Our platform is not intended for individuals under 18 years of age. We do not knowingly collect personal information from children.</p>

<h2>9. Changes to This Policy</h2>
<p>We may update this Privacy Policy from time to time. We will notify you of any changes by posting the new policy on this page and updating the effective date.</p>

<h2>10. Contact Us</h2>
<p>If you have questions about this Privacy Policy, please contact us at privacy@startupripple.com</p>
            ''',
            version='1.0',
            is_published=True,
            show_table_of_contents=True
        )


def remove_legal_pages(apps, schema_editor):
    """Remove seeded legal pages (reverse migration)."""
    LegalPage = apps.get_model('cms', 'LegalPage')
    LegalPage.objects.filter(page_type__in=['terms', 'investment_risk', 'privacy']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0003_legalpage'),
    ]

    operations = [
        migrations.RunPython(create_legal_pages, remove_legal_pages),
    ]
