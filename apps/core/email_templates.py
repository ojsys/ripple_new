"""
Unified email template system for StartUpRipple.
Provides consistent, beautiful email templates across the platform.
"""
from django.conf import settings


def get_base_email_template(title, subtitle, content, button_text=None, button_url=None,
                             footer_text=None, header_color="#26af59", icon="&#128274;"):
    """
    Generate a beautiful, responsive HTML email template.

    Args:
        title: Main heading of the email
        subtitle: Subheading below the title
        content: HTML content for the email body
        button_text: Optional CTA button text
        button_url: Optional CTA button URL
        footer_text: Optional custom footer message
        header_color: Header accent color (default: brand green)
        icon: Unicode/HTML entity for the icon (default: lock)

    Returns:
        Complete HTML email string
    """
    site_name = "StartUpRipple"
    year = "2024"

    button_html = ""
    if button_text and button_url:
        button_html = f'''
        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
            <tr>
                <td style="text-align: center; padding: 10px 0 30px 0;">
                    <a href="{button_url}"
                       style="display: inline-block; background-color: {header_color}; color: #ffffff; text-decoration: none; font-size: 16px; font-weight: 600; padding: 16px 40px; border-radius: 8px;">
                        {button_text}
                    </a>
                </td>
            </tr>
        </table>
        '''

    footer_message = footer_text or "This is an automated message from StartUpRipple."

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <title>{title}</title>
</head>
<body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7fa; -webkit-font-smoothing: antialiased;">
    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: #f4f7fa;">
        <tr>
            <td style="padding: 40px 20px;">
                <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="max-width: 600px; margin: 0 auto;">

                    <!-- Logo Header -->
                    <tr>
                        <td style="text-align: center; padding-bottom: 30px;">
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" style="margin: 0 auto;">
                                <tr>
                                    <td style="background-color: {header_color}; border-radius: 50%; width: 60px; height: 60px; text-align: center; vertical-align: middle;">
                                        <span style="color: #ffffff; font-size: 28px; font-weight: bold;">R</span>
                                    </td>
                                </tr>
                            </table>
                            <p style="margin: 15px 0 0 0; font-size: 24px; font-weight: 700; color: #1a1a2e;">{site_name}</p>
                        </td>
                    </tr>

                    <!-- Main Card -->
                    <tr>
                        <td>
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: #ffffff; border-radius: 16px; box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08);">

                                <!-- Header Bar -->
                                <tr>
                                    <td style="background-color: {header_color}; height: 8px; border-radius: 16px 16px 0 0;"></td>
                                </tr>

                                <!-- Content -->
                                <tr>
                                    <td style="padding: 40px 40px 20px 40px;">
                                        <!-- Icon -->
                                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                            <tr>
                                                <td style="text-align: center; padding-bottom: 25px;">
                                                    <table role="presentation" cellspacing="0" cellpadding="0" border="0" style="margin: 0 auto;">
                                                        <tr>
                                                            <td style="background-color: #e8f5ee; border-radius: 50%; width: 80px; height: 80px; text-align: center; vertical-align: middle;">
                                                                <span style="font-size: 36px;">{icon}</span>
                                                            </td>
                                                        </tr>
                                                    </table>
                                                </td>
                                            </tr>
                                        </table>

                                        <!-- Title -->
                                        <h1 style="margin: 0 0 10px 0; font-size: 26px; font-weight: 700; color: #1a1a2e; text-align: center;">{title}</h1>
                                        <p style="margin: 0 0 25px 0; font-size: 14px; color: #718096; text-align: center;">{subtitle}</p>

                                        <!-- Main Content -->
                                        {content}

                                        <!-- CTA Button -->
                                        {button_html}
                                    </td>
                                </tr>

                                <!-- Card Footer -->
                                <tr>
                                    <td style="padding: 0 40px 40px 40px;">
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="padding: 30px 20px; text-align: center;">
                            <p style="margin: 0 0 20px 0; font-size: 13px; color: #a0aec0;">
                                {footer_message}
                            </p>
                            <p style="margin: 0; font-size: 13px; color: #a0aec0;">
                                &copy; {year} {site_name}. All rights reserved.
                            </p>
                        </td>
                    </tr>

                </table>
            </td>
        </tr>
    </table>
</body>
</html>'''


def get_info_box(title, rows, color="#26af59"):
    """
    Generate an info box with key-value rows.

    Args:
        title: Box title
        rows: List of tuples [(label, value), ...]
        color: Accent color

    Returns:
        HTML string for the info box
    """
    rows_html = ""
    for label, value in rows:
        rows_html += f'''
        <tr>
            <td style="padding: 10px 0; border-bottom: 1px solid #e2e8f0; color: #718096; font-size: 14px;">{label}</td>
            <td style="padding: 10px 0; border-bottom: 1px solid #e2e8f0; color: #1a1a2e; font-weight: 600; font-size: 14px; text-align: right;">{value}</td>
        </tr>'''

    return f'''
    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: #f7fafc; border-radius: 8px; border-left: 4px solid {color}; margin: 20px 0;">
        <tr>
            <td style="padding: 20px;">
                <p style="margin: 0 0 15px 0; font-size: 14px; font-weight: 600; color: {color};">{title}</p>
                <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                    {rows_html}
                </table>
            </td>
        </tr>
    </table>'''


def get_warning_box(message):
    """Generate a warning/info box."""
    return f'''
    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: #fff8e6; border-radius: 8px; border-left: 4px solid #f6ad55; margin: 20px 0;">
        <tr>
            <td style="padding: 15px 20px;">
                <p style="margin: 0; font-size: 14px; line-height: 1.6; color: #744210;">
                    {message}
                </p>
            </td>
        </tr>
    </table>'''


def get_success_box(message):
    """Generate a success box."""
    return f'''
    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: #d1fae5; border-radius: 8px; border-left: 4px solid #059669; margin: 20px 0;">
        <tr>
            <td style="padding: 15px 20px;">
                <p style="margin: 0; font-size: 14px; line-height: 1.6; color: #065f46;">
                    {message}
                </p>
            </td>
        </tr>
    </table>'''


def get_highlight_box(label, value, color="#26af59"):
    """Generate a highlighted amount/value box."""
    return f'''
    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: {color}; border-radius: 12px; margin: 20px 0;">
        <tr>
            <td style="padding: 25px; text-align: center;">
                <p style="margin: 0 0 5px 0; font-size: 14px; color: rgba(255,255,255,0.9);">{label}</p>
                <p style="margin: 0; font-size: 32px; font-weight: 700; color: #ffffff;">{value}</p>
            </td>
        </tr>
    </table>'''


def get_link_box(url):
    """Generate a copyable link box."""
    return f'''
    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: #f7fafc; border-radius: 6px; border: 1px solid #e2e8f0; margin: 15px 0;">
        <tr>
            <td style="padding: 12px 15px;">
                <p style="margin: 0; font-size: 13px; line-height: 1.6; color: #26af59; text-align: center; word-break: break-all;">
                    {url}
                </p>
            </td>
        </tr>
    </table>'''


def get_account_box(label, value):
    """Generate an account info box."""
    return f'''
    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: #f7fafc; border-radius: 8px; margin: 20px 0;">
        <tr>
            <td style="padding: 20px;">
                <p style="margin: 0 0 8px 0; font-size: 13px; color: #718096; text-align: center;">
                    {label}
                </p>
                <p style="margin: 0; font-size: 15px; font-weight: 600; color: #1a1a2e; text-align: center;">
                    {value}
                </p>
            </td>
        </tr>
    </table>'''


# Email Icons (Unicode entities)
ICONS = {
    'lock': '&#128274;',
    'email': '&#9993;',
    'check': '&#9989;',
    'wave': '&#128075;',
    'rocket': '&#128640;',
    'money': '&#128176;',
    'gift': '&#127873;',
    'star': '&#11088;',
    'bell': '&#128276;',
    'warning': '&#9888;',
    'success': '&#9989;',
    'celebrate': '&#127881;',
    'key': '&#128273;',
    'shield': '&#128737;',
    'heart': '&#10084;',
    'thumbs_up': '&#128077;',
    'document': '&#128196;',
    'calendar': '&#128197;',
    'clock': '&#128336;',
    'bank': '&#127974;',
}
