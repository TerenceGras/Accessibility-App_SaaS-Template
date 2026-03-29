#!/usr/bin/env python3
"""
LumTrails Mailing Service - Subscription Upgrade Email Templates

Email-client-friendly subscription emails using table-based layout
"""
from .base_template import get_base_template, get_button_html, get_info_box_html, get_feature_item_html
from config import FRONTEND_URL


def get_subscription_upgrade_email(name: str, old_tier: str, new_tier: str, interval: str = "monthly", language: str = "en") -> dict:
    """
    Generate subscription upgrade confirmation email
    
    Args:
        name: User's display name
        old_tier: Previous subscription tier
        new_tier: New subscription tier
        interval: Billing interval ('monthly' or 'yearly')
        language: User's preferred language
    
    Returns:
        Dict with subject and html_content
    """
    # Tier display names for each language
    tier_names = {
        "en": {"free": "Free", "standard": "Standard", "business": "Business"},
        "fr": {"free": "Gratuit", "standard": "Standard", "business": "Business"},
        "de": {"free": "Kostenlos", "standard": "Standard", "business": "Business"},
        "es": {"free": "Gratis", "standard": "Estándar", "business": "Business"},
        "it": {"free": "Gratuito", "standard": "Standard", "business": "Business"},
        "pt": {"free": "Gratuito", "standard": "Standard", "business": "Business"}
    }
    
    # Interval display names for each language
    interval_names = {
        "en": {"monthly": "Monthly", "yearly": "Yearly"},
        "fr": {"monthly": "Mensuel", "yearly": "Annuel"},
        "de": {"monthly": "Monatlich", "yearly": "Jährlich"},
        "es": {"monthly": "Mensual", "yearly": "Anual"},
        "it": {"monthly": "Mensile", "yearly": "Annuale"},
        "pt": {"monthly": "Mensal", "yearly": "Anual"}
    }
    
    templates = {
        "en": {
            "subject": f"Welcome to {tier_names['en'].get(new_tier, new_tier)} Plan! 🚀",
            "greeting": f"Great news, {name}!" if name else "Great news!",
            "intro": "Your subscription has been successfully upgraded.",
            "upgrade_summary": "Upgrade Summary",
            "from_plan": "Previous plan",
            "to_plan": "New plan",
            "billing_interval": "Billing",
            "new_features": "Your New Features",
            "standard_features": [
                "Unlimited web scans",
                "Unlimited PDF scans",
                "API access with 100 calls/month",
                "Priority support"
            ],
            "business_features": [
                "Everything in Standard, plus:",
                "Unlimited API calls",
                "Team collaboration features",
                "Slack, Notion, and GitHub integrations",
                "White-label reports",
                "Dedicated support"
            ],
            "cta": "Start Using Your New Features",
            "billing_note": "Your subscription will automatically renew. You can manage your billing settings anytime.",
            "thanks": "Thank you for upgrading and supporting accessible web development!"
        },
        "fr": {
            "subject": f"Bienvenue dans le plan {tier_names['fr'].get(new_tier, new_tier)} ! 🚀",
            "greeting": f"Excellente nouvelle, {name} !" if name else "Excellente nouvelle !",
            "intro": "Votre abonnement a été mis à niveau avec succès.",
            "upgrade_summary": "Résumé de la mise à niveau",
            "from_plan": "Plan précédent",
            "to_plan": "Nouveau plan",
            "billing_interval": "Facturation",
            "new_features": "Vos nouvelles fonctionnalités",
            "standard_features": [
                "Analyses web illimitées",
                "Analyses PDF illimitées",
                "Accès API avec 100 appels/mois",
                "Support prioritaire"
            ],
            "business_features": [
                "Tout de Standard, plus :",
                "Appels API illimités",
                "Fonctionnalités de collaboration en équipe",
                "Intégrations Slack, Notion et GitHub",
                "Rapports en marque blanche",
                "Support dédié"
            ],
            "cta": "Commencez à utiliser vos nouvelles fonctionnalités",
            "billing_note": "Votre abonnement se renouvellera automatiquement. Vous pouvez gérer vos paramètres de facturation à tout moment.",
            "thanks": "Merci pour votre mise à niveau et votre soutien au développement web accessible !"
        },
        "de": {
            "subject": f"Willkommen zum {tier_names['de'].get(new_tier, new_tier)} Plan! 🚀",
            "greeting": f"Tolle Neuigkeiten, {name}!" if name else "Tolle Neuigkeiten!",
            "intro": "Ihr Abonnement wurde erfolgreich aktualisiert.",
            "upgrade_summary": "Upgrade-Zusammenfassung",
            "from_plan": "Vorheriger Plan",
            "to_plan": "Neuer Plan",
            "billing_interval": "Abrechnung",
            "new_features": "Ihre neuen Funktionen",
            "standard_features": [
                "Unbegrenzte Web-Scans",
                "Unbegrenzte PDF-Scans",
                "API-Zugang mit 100 Aufrufen/Monat",
                "Prioritäts-Support"
            ],
            "business_features": [
                "Alles aus Standard, plus:",
                "Unbegrenzte API-Aufrufe",
                "Team-Zusammenarbeitsfunktionen",
                "Slack-, Notion- und GitHub-Integrationen",
                "White-Label-Berichte",
                "Dedizierter Support"
            ],
            "cta": "Nutzen Sie Ihre neuen Funktionen",
            "billing_note": "Ihr Abonnement wird automatisch verlängert. Sie können Ihre Abrechnungseinstellungen jederzeit verwalten.",
            "thanks": "Vielen Dank für Ihr Upgrade und Ihre Unterstützung für barrierefreie Webentwicklung!"
        },
        "es": {
            "subject": f"¡Bienvenido al plan {tier_names['es'].get(new_tier, new_tier)}! 🚀",
            "greeting": f"¡Excelentes noticias, {name}!" if name else "¡Excelentes noticias!",
            "intro": "Tu suscripción ha sido actualizada exitosamente.",
            "upgrade_summary": "Resumen de la actualización",
            "from_plan": "Plan anterior",
            "to_plan": "Nuevo plan",
            "billing_interval": "Facturación",
            "new_features": "Tus nuevas funcionalidades",
            "standard_features": [
                "Escaneos web ilimitados",
                "Escaneos PDF ilimitados",
                "Acceso API con 100 llamadas/mes",
                "Soporte prioritario"
            ],
            "business_features": [
                "Todo lo de Standard, más:",
                "Llamadas API ilimitadas",
                "Funciones de colaboración en equipo",
                "Integraciones con Slack, Notion y GitHub",
                "Informes con marca blanca",
                "Soporte dedicado"
            ],
            "cta": "Empieza a usar tus nuevas funcionalidades",
            "billing_note": "Tu suscripción se renovará automáticamente. Puedes gestionar tu configuración de facturación en cualquier momento.",
            "thanks": "¡Gracias por actualizar y apoyar el desarrollo web accesible!"
        },
        "it": {
            "subject": f"Benvenuto nel piano {tier_names['it'].get(new_tier, new_tier)}! 🚀",
            "greeting": f"Ottime notizie, {name}!" if name else "Ottime notizie!",
            "intro": "Il tuo abbonamento è stato aggiornato con successo.",
            "upgrade_summary": "Riepilogo dell'aggiornamento",
            "from_plan": "Piano precedente",
            "to_plan": "Nuovo piano",
            "billing_interval": "Fatturazione",
            "new_features": "Le tue nuove funzionalità",
            "standard_features": [
                "Scansioni web illimitate",
                "Scansioni PDF illimitate",
                "Accesso API con 100 chiamate/mese",
                "Supporto prioritario"
            ],
            "business_features": [
                "Tutto di Standard, più:",
                "Chiamate API illimitate",
                "Funzionalità di collaborazione in team",
                "Integrazioni Slack, Notion e GitHub",
                "Report white-label",
                "Supporto dedicato"
            ],
            "cta": "Inizia a usare le tue nuove funzionalità",
            "billing_note": "Il tuo abbonamento si rinnoverà automaticamente. Puoi gestire le impostazioni di fatturazione in qualsiasi momento.",
            "thanks": "Grazie per l'aggiornamento e il supporto allo sviluppo web accessibile!"
        },
        "pt": {
            "subject": f"Bem-vindo ao plano {tier_names['pt'].get(new_tier, new_tier)}! 🚀",
            "greeting": f"Ótimas notícias, {name}!" if name else "Ótimas notícias!",
            "intro": "A sua subscrição foi atualizada com sucesso.",
            "upgrade_summary": "Resumo da atualização",
            "from_plan": "Plano anterior",
            "to_plan": "Novo plano",
            "billing_interval": "Faturação",
            "new_features": "As suas novas funcionalidades",
            "standard_features": [
                "Análises web ilimitadas",
                "Análises PDF ilimitadas",
                "Acesso à API com 100 chamadas/mês",
                "Suporte prioritário"
            ],
            "business_features": [
                "Tudo do Standard, mais:",
                "Chamadas API ilimitadas",
                "Funcionalidades de colaboração em equipa",
                "Integrações Slack, Notion e GitHub",
                "Relatórios white-label",
                "Suporte dedicado"
            ],
            "cta": "Comece a usar as suas novas funcionalidades",
            "billing_note": "A sua subscrição será renovada automaticamente. Pode gerir as suas configurações de faturação a qualquer momento.",
            "thanks": "Obrigado pela atualização e pelo apoio ao desenvolvimento web acessível!"
        }
    }
    
    t = templates.get(language, templates["en"])
    tier_display = tier_names.get(language, tier_names["en"])
    interval_display = interval_names.get(language, interval_names["en"])
    
    # Get features based on new tier
    features = t["business_features"] if new_tier == "business" else t["standard_features"]
    features_html = "".join([f'<li style="padding: 8px 0; color: #4b5563;">✓ {f}</li>' for f in features])
    
    content = f"""
        <h1 style="color: #111827; font-size: 24px; font-weight: 700; margin: 0 0 24px 0;">{t['greeting']}</h1>
        <p style="color: #4b5563; font-size: 16px; margin: 0 0 16px 0;">{t['intro']}</p>
        
        <!-- Upgrade Summary Box -->
        <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="margin: 24px 0; background-color: #f0f9ff; border-radius: 8px;">
            <tr>
                <td style="padding: 20px;">
                    <p style="margin: 0 0 12px 0; font-weight: 600; color: #0284c7; font-size: 14px; text-transform: uppercase;">{t['upgrade_summary']}</p>
                    <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
                        <tr>
                            <td style="padding: 8px 0; color: #6b7280;">{t['from_plan']}:</td>
                            <td style="padding: 8px 0; color: #111827; font-weight: 600; text-align: right;">{tier_display.get(old_tier, old_tier)}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; color: #6b7280;">{t['to_plan']}:</td>
                            <td style="padding: 8px 0; color: #0284c7; font-weight: 700; text-align: right;">{tier_display.get(new_tier, new_tier)}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; color: #6b7280;">{t['billing_interval']}:</td>
                            <td style="padding: 8px 0; color: #111827; font-weight: 600; text-align: right;">{interval_display.get(interval, interval)}</td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
        
        <h2 style="color: #111827; font-size: 20px; font-weight: 600; margin: 32px 0 16px 0;">{t['new_features']}</h2>
        
        <ul style="margin: 0; padding: 0 0 0 20px; list-style: none;">
            {features_html}
        </ul>
        
        <div style="text-align: center;">
            {get_button_html(t['cta'], f"{FRONTEND_URL}/scan")}
        </div>
        
        <p style="color: #9ca3af; font-size: 14px; margin: 24px 0 8px 0;">{t['billing_note']}</p>
        <p style="color: #0284c7; font-size: 14px; margin: 0;">{t['thanks']}</p>
    """
    
    return {
        "subject": t["subject"],
        "html_content": get_base_template(content, language)
    }
