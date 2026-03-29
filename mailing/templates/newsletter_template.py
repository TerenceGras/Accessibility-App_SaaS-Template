#!/usr/bin/env python3
"""
LumTrails Mailing Service - Newsletter Email Templates
"""
from .base_template import get_base_template
from config import FRONTEND_URL


def get_newsletter_email(
    subject: str,
    content_html: str,
    name: str = None,
    language: str = "en"
) -> dict:
    """
    Generate newsletter email with custom content
    
    Args:
        subject: Email subject line
        content_html: HTML content for the newsletter body
        name: Optional recipient name for personalization
        language: Language code for footer translations
    
    Returns:
        Dict with subject and html_content
    """
    greetings = {
        "en": f"Hi {name}!" if name else "Hi there!",
        "fr": f"Bonjour {name} !" if name else "Bonjour !",
        "de": f"Hallo {name}!" if name else "Hallo!",
        "es": f"¡Hola {name}!" if name else "¡Hola!",
        "it": f"Ciao {name}!" if name else "Ciao!",
        "pt": f"Olá {name}!" if name else "Olá!"
    }
    
    unsubscribe_text = {
        "en": "You received this email because you're subscribed to LumTrails updates. If you no longer wish to receive these emails,",
        "fr": "Vous avez reçu cet e-mail car vous êtes abonné aux mises à jour LumTrails. Si vous ne souhaitez plus recevoir ces e-mails,",
        "de": "Sie haben diese E-Mail erhalten, weil Sie LumTrails-Updates abonniert haben. Wenn Sie diese E-Mails nicht mehr erhalten möchten,",
        "es": "Recibiste este correo porque estás suscrito a las actualizaciones de LumTrails. Si ya no deseas recibir estos correos,",
        "it": "Hai ricevuto questa email perché sei iscritto agli aggiornamenti di LumTrails. Se non desideri più ricevere queste email,",
        "pt": "Recebeu este email porque está inscrito nas atualizações do LumTrails. Se não deseja mais receber estes emails,"
    }
    
    unsubscribe_link_text = {
        "en": "unsubscribe here",
        "fr": "désabonnez-vous ici",
        "de": "melden Sie sich hier ab",
        "es": "cancela tu suscripción aquí",
        "it": "cancella l'iscrizione qui",
        "pt": "cancele a inscrição aqui"
    }
    
    greeting = greetings.get(language, greetings["en"])
    unsub_text = unsubscribe_text.get(language, unsubscribe_text["en"])
    unsub_link = unsubscribe_link_text.get(language, unsubscribe_link_text["en"])
    
    content = f"""
        <p style="font-size: 18px; color: #111827;">{greeting}</p>
        
        {content_html}
        
        <div style="margin-top: 32px; padding-top: 24px; border-top: 1px solid #e5e7eb;">
            <p style="color: #9ca3af; font-size: 12px; line-height: 1.5;">
                {unsub_text} <a href="{FRONTEND_URL}/settings/notifications" style="color: #0ea5e9;">{unsub_link}</a>.
            </p>
        </div>
    """
    
    return {
        "subject": subject,
        "html_content": get_base_template(content, language)
    }


def get_product_update_email(
    title: str,
    features: list[dict],
    name: str = None,
    language: str = "en"
) -> dict:
    """
    Generate product update/feature announcement email
    
    Args:
        title: Update title/headline
        features: List of dicts with 'title', 'description', and optional 'icon'
        name: Optional recipient name
        language: Language code
    
    Returns:
        Dict with subject and html_content
    """
    intro_text = {
        "en": "We've been working hard to make LumTrails even better. Here's what's new:",
        "fr": "Nous avons travaillé dur pour améliorer LumTrails. Voici les nouveautés :",
        "de": "Wir haben hart daran gearbeitet, LumTrails noch besser zu machen. Hier sind die Neuigkeiten:",
        "es": "Hemos trabajado duro para mejorar LumTrails. Esto es lo nuevo:",
        "it": "Abbiamo lavorato duramente per migliorare LumTrails. Ecco le novità:",
        "pt": "Trabalhámos arduamente para melhorar o LumTrails. Aqui está o que há de novo:"
    }
    
    cta_text = {
        "en": "Try It Now",
        "fr": "Essayez maintenant",
        "de": "Jetzt ausprobieren",
        "es": "Pruébalo ahora",
        "it": "Provalo ora",
        "pt": "Experimente agora"
    }
    
    intro = intro_text.get(language, intro_text["en"])
    cta = cta_text.get(language, cta_text["en"])
    
    features_html = ""
    for feature in features:
        icon = feature.get("icon", "✨")
        features_html += f"""
            <div style="margin-bottom: 24px; padding: 16px; background: #f9fafb; border-radius: 8px;">
                <div style="font-size: 24px; margin-bottom: 8px;">{icon}</div>
                <h3 style="color: #111827; font-size: 18px; margin: 0 0 8px 0;">{feature['title']}</h3>
                <p style="color: #6b7280; margin: 0;">{feature['description']}</p>
            </div>
        """
    
    content_html = f"""
        <h1 style="color: #111827; font-size: 28px; margin-bottom: 16px;">{title}</h1>
        <p style="color: #6b7280; margin-bottom: 32px;">{intro}</p>
        
        {features_html}
        
        <div style="text-align: center; margin: 32px 0;">
            <a href="{FRONTEND_URL}/dashboard" class="button">{cta}</a>
        </div>
    """
    
    return get_newsletter_email(
        subject=f"🆕 {title}",
        content_html=content_html,
        name=name,
        language=language
    )
