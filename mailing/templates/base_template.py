#!/usr/bin/env python3
"""
LumTrails Mailing Service - Base Email Template

This template is designed for maximum email client compatibility:
- Table-based layout (works in Outlook, Gmail, Yahoo, etc.)
- All inline styles (CSS classes not reliably supported)
- No CSS gradients or advanced features
- Proper image handling with alt text
"""
from config import LOGO_URL, FRONTEND_URL, CONTACT_EMAIL


def get_base_template(content: str, language: str = "en") -> str:
    """
    Base HTML email template with LumTrails branding
    
    Uses table-based layout and inline styles for maximum
    email client compatibility (Gmail, Outlook, Yahoo, Apple Mail, etc.)
    
    Args:
        content: The main content HTML to inject
        language: Language code for footer text
        
    Returns:
        Complete HTML email
    """
    footer_texts = {
        "en": {
            "unsubscribe": "You received this email because you have an account with LumTrails.",
            "contact": "Questions? Contact us at",
            "rights": "All rights reserved."
        },
        "fr": {
            "unsubscribe": "Vous avez reçu cet e-mail car vous avez un compte LumTrails.",
            "contact": "Des questions ? Contactez-nous à",
            "rights": "Tous droits réservés."
        },
        "de": {
            "unsubscribe": "Sie haben diese E-Mail erhalten, weil Sie ein Konto bei LumTrails haben.",
            "contact": "Fragen? Kontaktieren Sie uns unter",
            "rights": "Alle Rechte vorbehalten."
        },
        "es": {
            "unsubscribe": "Ha recibido este correo porque tiene una cuenta en LumTrails.",
            "contact": "¿Preguntas? Contáctenos en",
            "rights": "Todos los derechos reservados."
        },
        "it": {
            "unsubscribe": "Hai ricevuto questa email perché hai un account LumTrails.",
            "contact": "Domande? Contattaci a",
            "rights": "Tutti i diritti riservati."
        },
        "pt": {
            "unsubscribe": "Recebeu este e-mail porque tem uma conta LumTrails.",
            "contact": "Dúvidas? Contacte-nos em",
            "rights": "Todos os direitos reservados."
        }
    }
    
    texts = footer_texts.get(language, footer_texts["en"])
    year = "2025"
    
    # Table-based layout for email client compatibility
    # Note: We use text-based branding instead of images to avoid spam filters
    # and ensure the logo displays correctly without requiring user action
    return f"""<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" lang="{language}">
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta name="x-apple-disable-message-reformatting" />
    <meta name="format-detection" content="telephone=no, date=no, address=no, email=no" />
    <title>LumTrails</title>
    <!--[if mso]>
    <style type="text/css">
        body, table, td {{font-family: Arial, Helvetica, sans-serif !important;}}
    </style>
    <![endif]-->
</head>
<body style="margin: 0; padding: 0; background-color: #f3f4f6; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; -webkit-font-smoothing: antialiased;">
    <!-- Wrapper Table -->
    <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background-color: #f3f4f6;">
        <tr>
            <td align="center" style="padding: 40px 20px;">
                <!-- Main Content Table -->
                <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="600" style="max-width: 600px; background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    
                    <!-- Header - Simple text-based branding -->
                    <tr>
                        <td style="padding: 24px 40px; border-bottom: 1px solid #e5e7eb;">
                            <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
                                <tr>
                                    <td>
                                        <a href="{FRONTEND_URL}" style="text-decoration: none; display: inline-block;">
                                            <span style="font-size: 24px; font-weight: 700; color: #0284c7; letter-spacing: -0.5px;">Lum</span><span style="font-size: 24px; font-weight: 700; color: #1e293b; letter-spacing: -0.5px;">Trails</span>
                                        </a>
                                    </td>
                                    <td align="right" style="color: #9ca3af; font-size: 12px;">
                                        Web Accessibility
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Content -->
                    <tr>
                        <td style="padding: 40px; color: #1f2937; font-size: 16px; line-height: 1.6;">
                            {content}
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #f9fafb; border-top: 1px solid #e5e7eb; padding: 32px 40px; text-align: center;">
                            <p style="margin: 0 0 8px 0; color: #6b7280; font-size: 14px; line-height: 1.5;">
                                {texts['unsubscribe']}
                            </p>
                            <p style="margin: 0 0 8px 0; color: #6b7280; font-size: 14px; line-height: 1.5;">
                                {texts['contact']} <a href="mailto:{CONTACT_EMAIL}" style="color: #0284c7; text-decoration: none;">{CONTACT_EMAIL}</a>
                            </p>
                            <p style="margin: 0; color: #9ca3af; font-size: 12px; line-height: 1.5;">
                                &copy; {year} LumTrails. {texts['rights']}
                            </p>
                        </td>
                    </tr>
                    
                </table>
                <!-- End Main Content Table -->
            </td>
        </tr>
    </table>
    <!-- End Wrapper Table -->
</body>
</html>"""


def get_button_html(text: str, url: str, color: str = "#0284c7") -> str:
    """
    Generate email-safe button HTML
    
    Uses table-based approach for Outlook compatibility
    """
    return f"""<table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin: 24px 0;">
        <tr>
            <td align="center" style="border-radius: 8px; background-color: {color};">
                <a href="{url}" target="_blank" style="display: inline-block; padding: 14px 32px; font-size: 16px; font-weight: 600; color: #ffffff; text-decoration: none; border-radius: 8px;">
                    {text}
                </a>
            </td>
        </tr>
    </table>"""


def get_code_box_html(label: str, code: str) -> str:
    """
    Generate email-safe verification code box
    """
    return f"""<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="margin: 24px 0;">
        <tr>
            <td align="center" style="background-color: #f3f4f6; border: 2px dashed #d1d5db; border-radius: 12px; padding: 24px;">
                <p style="margin: 0 0 8px 0; color: #6b7280; font-size: 14px;">{label}</p>
                <p style="margin: 0; font-size: 36px; font-weight: 700; letter-spacing: 8px; color: #0284c7; font-family: Monaco, 'Courier New', monospace;">
                    {code}
                </p>
            </td>
        </tr>
    </table>"""


def get_info_box_html(content: str) -> str:
    """
    Generate email-safe info box (blue left border)
    """
    return f"""<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="margin: 24px 0;">
        <tr>
            <td style="background-color: #eff6ff; border-left: 4px solid #0284c7; padding: 16px 20px; border-radius: 0 8px 8px 0;">
                <p style="margin: 0; color: #1e40af; font-size: 14px; line-height: 1.5;">{content}</p>
            </td>
        </tr>
    </table>"""


def get_warning_box_html(content: str) -> str:
    """
    Generate email-safe warning box (amber left border)
    """
    return f"""<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="margin: 24px 0;">
        <tr>
            <td style="background-color: #fef3c7; border-left: 4px solid #f59e0b; padding: 16px 20px; border-radius: 0 8px 8px 0;">
                <p style="margin: 0; color: #92400e; font-size: 14px; line-height: 1.5;">{content}</p>
            </td>
        </tr>
    </table>"""


def get_feature_item_html(icon: str, title: str, description: str) -> str:
    """
    Generate email-safe feature list item
    """
    return f"""<tr>
        <td style="padding: 12px 0; border-bottom: 1px solid #e5e7eb;">
            <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
                <tr>
                    <td width="40" valign="top" style="font-size: 20px; padding-right: 12px;">{icon}</td>
                    <td valign="top">
                        <p style="margin: 0 0 4px 0; font-weight: 600; color: #111827;">{title}</p>
                        <p style="margin: 0; color: #6b7280; font-size: 14px;">{description}</p>
                    </td>
                </tr>
            </table>
        </td>
    </tr>"""
