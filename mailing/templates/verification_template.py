#!/usr/bin/env python3
"""
LumTrails Mailing Service - Verification Email Templates

Email-client-friendly verification emails using table-based layout
"""
from .base_template import get_base_template, get_code_box_html, get_warning_box_html
from config import VERIFICATION_CODE_EXPIRY_MINUTES


def get_verification_email(code: str, name: str = "", language: str = "en") -> dict:
    """
    Generate verification email content
    
    Returns:
        Dict with subject and html_content
    """
    templates = {
        "en": {
            "subject": "Verify your LumTrails account",
            "greeting": f"Hi {name}," if name else "Hi there,",
            "intro": "Thank you for creating a LumTrails account! Please use the verification code below to confirm your email address:",
            "code_label": "Your verification code",
            "expiry": f"This code will expire in {VERIFICATION_CODE_EXPIRY_MINUTES} minutes.",
            "ignore": "If you didn't create a LumTrails account, you can safely ignore this email."
        },
        "fr": {
            "subject": "Vérifiez votre compte LumTrails",
            "greeting": f"Bonjour {name}," if name else "Bonjour,",
            "intro": "Merci d'avoir créé un compte LumTrails ! Veuillez utiliser le code de vérification ci-dessous pour confirmer votre adresse e-mail :",
            "code_label": "Votre code de vérification",
            "expiry": f"Ce code expirera dans {VERIFICATION_CODE_EXPIRY_MINUTES} minutes.",
            "ignore": "Si vous n'avez pas créé de compte LumTrails, vous pouvez ignorer cet e-mail."
        },
        "de": {
            "subject": "Bestätigen Sie Ihr LumTrails-Konto",
            "greeting": f"Hallo {name}," if name else "Hallo,",
            "intro": "Vielen Dank für die Erstellung eines LumTrails-Kontos! Bitte verwenden Sie den folgenden Bestätigungscode, um Ihre E-Mail-Adresse zu bestätigen:",
            "code_label": "Ihr Bestätigungscode",
            "expiry": f"Dieser Code läuft in {VERIFICATION_CODE_EXPIRY_MINUTES} Minuten ab.",
            "ignore": "Wenn Sie kein LumTrails-Konto erstellt haben, können Sie diese E-Mail ignorieren."
        },
        "es": {
            "subject": "Verifica tu cuenta de LumTrails",
            "greeting": f"Hola {name}," if name else "Hola,",
            "intro": "¡Gracias por crear una cuenta de LumTrails! Por favor, utiliza el código de verificación a continuación para confirmar tu dirección de correo electrónico:",
            "code_label": "Tu código de verificación",
            "expiry": f"Este código expirará en {VERIFICATION_CODE_EXPIRY_MINUTES} minutos.",
            "ignore": "Si no creaste una cuenta de LumTrails, puedes ignorar este correo."
        },
        "it": {
            "subject": "Verifica il tuo account LumTrails",
            "greeting": f"Ciao {name}," if name else "Ciao,",
            "intro": "Grazie per aver creato un account LumTrails! Utilizza il codice di verifica qui sotto per confermare il tuo indirizzo email:",
            "code_label": "Il tuo codice di verifica",
            "expiry": f"Questo codice scadrà tra {VERIFICATION_CODE_EXPIRY_MINUTES} minuti.",
            "ignore": "Se non hai creato un account LumTrails, puoi ignorare questa email."
        },
        "pt": {
            "subject": "Verifique a sua conta LumTrails",
            "greeting": f"Olá {name}," if name else "Olá,",
            "intro": "Obrigado por criar uma conta LumTrails! Por favor, utilize o código de verificação abaixo para confirmar o seu endereço de e-mail:",
            "code_label": "O seu código de verificação",
            "expiry": f"Este código expirará em {VERIFICATION_CODE_EXPIRY_MINUTES} minutos.",
            "ignore": "Se não criou uma conta LumTrails, pode ignorar este e-mail."
        }
    }
    
    t = templates.get(language, templates["en"])
    
    # Build content using inline styles (no CSS classes)
    content = f"""
        <h1 style="color: #111827; font-size: 24px; font-weight: 700; margin: 0 0 24px 0;">{t['greeting']}</h1>
        <p style="color: #4b5563; font-size: 16px; margin: 0 0 16px 0;">{t['intro']}</p>
        
        {get_code_box_html(t['code_label'], code)}
        
        {get_warning_box_html(f"⏱️ {t['expiry']}")}
        
        <p style="color: #9ca3af; font-size: 14px; margin: 24px 0 0 0;">{t['ignore']}</p>
    """
    
    return {
        "subject": t["subject"],
        "html_content": get_base_template(content, language)
    }
