#!/usr/bin/env python3
"""
LumTrails Mailing Service - Welcome Email Templates

Email-client-friendly welcome emails using table-based layout
"""
from .base_template import get_base_template, get_button_html, get_info_box_html, get_feature_item_html
from config import FRONTEND_URL


def get_welcome_email(name: str = "", language: str = "en") -> dict:
    """
    Generate welcome email content for verified users
    
    Returns:
        Dict with subject and html_content
    """
    templates = {
        "en": {
            "subject": "Welcome to LumTrails! 🎉",
            "greeting": f"Welcome aboard, {name}!" if name else "Welcome aboard!",
            "intro": "Your account has been verified and you're all set to start improving your website and PDF accessibility.",
            "getting_started": "Get Started in 3 Easy Steps",
            "step1_title": "1. Scan a Website",
            "step1_desc": "Enter any URL to run a comprehensive WCAG 2.1 AA accessibility analysis with 5 powerful scanning engines.",
            "step2_title": "2. Scan a PDF",
            "step2_desc": "Upload a PDF document for AI-powered accessibility analysis using GPT vision technology.",
            "step3_title": "3. Review & Fix",
            "step3_desc": "Get actionable recommendations to fix accessibility issues and track your progress over time.",
            "free_credits": "Your Free Plan Credits",
            "web_credits": "5 web scan credits per day",
            "pdf_credits": "1 PDF scan credit per week",
            "upgrade_note": "Need more? Upgrade to Standard or Business for unlimited scans, API access, and integrations.",
            "cta": "Start Your First Scan",
            "help": "Need help getting started? Check out our documentation or contact our support team."
        },
        "fr": {
            "subject": "Bienvenue sur LumTrails ! 🎉",
            "greeting": f"Bienvenue, {name} !" if name else "Bienvenue !",
            "intro": "Votre compte a été vérifié et vous êtes prêt à améliorer l'accessibilité de vos sites web et documents PDF.",
            "getting_started": "Commencez en 3 étapes simples",
            "step1_title": "1. Analysez un site web",
            "step1_desc": "Entrez n'importe quelle URL pour effectuer une analyse d'accessibilité WCAG 2.1 AA complète avec 5 moteurs d'analyse puissants.",
            "step2_title": "2. Analysez un PDF",
            "step2_desc": "Téléchargez un document PDF pour une analyse d'accessibilité alimentée par l'IA avec la technologie GPT vision.",
            "step3_title": "3. Examinez et corrigez",
            "step3_desc": "Obtenez des recommandations exploitables pour corriger les problèmes d'accessibilité et suivre vos progrès.",
            "free_credits": "Vos crédits gratuits",
            "web_credits": "5 crédits d'analyse web par jour",
            "pdf_credits": "1 crédit d'analyse PDF par semaine",
            "upgrade_note": "Besoin de plus ? Passez à Standard ou Business pour des analyses illimitées, l'accès API et les intégrations.",
            "cta": "Lancez votre première analyse",
            "help": "Besoin d'aide ? Consultez notre documentation ou contactez notre équipe de support."
        },
        "de": {
            "subject": "Willkommen bei LumTrails! 🎉",
            "greeting": f"Willkommen an Bord, {name}!" if name else "Willkommen an Bord!",
            "intro": "Ihr Konto wurde verifiziert und Sie können jetzt mit der Verbesserung der Barrierefreiheit Ihrer Websites und PDF-Dokumente beginnen.",
            "getting_started": "Starten Sie in 3 einfachen Schritten",
            "step1_title": "1. Website scannen",
            "step1_desc": "Geben Sie eine beliebige URL ein, um eine umfassende WCAG 2.1 AA Barrierefreiheitsanalyse mit 5 leistungsstarken Scan-Engines durchzuführen.",
            "step2_title": "2. PDF scannen",
            "step2_desc": "Laden Sie ein PDF-Dokument für eine KI-gestützte Barrierefreiheitsanalyse mit GPT-Vision-Technologie hoch.",
            "step3_title": "3. Überprüfen & Beheben",
            "step3_desc": "Erhalten Sie umsetzbare Empfehlungen zur Behebung von Barrierefreiheitsproblemen und verfolgen Sie Ihren Fortschritt.",
            "free_credits": "Ihre kostenlosen Credits",
            "web_credits": "5 Web-Scan-Credits pro Tag",
            "pdf_credits": "1 PDF-Scan-Credit pro Woche",
            "upgrade_note": "Mehr benötigt? Upgraden Sie auf Standard oder Business für unbegrenzte Scans, API-Zugang und Integrationen.",
            "cta": "Starten Sie Ihren ersten Scan",
            "help": "Brauchen Sie Hilfe? Schauen Sie in unsere Dokumentation oder kontaktieren Sie unser Support-Team."
        },
        "es": {
            "subject": "¡Bienvenido a LumTrails! 🎉",
            "greeting": f"¡Bienvenido, {name}!" if name else "¡Bienvenido!",
            "intro": "Tu cuenta ha sido verificada y estás listo para empezar a mejorar la accesibilidad de tus sitios web y documentos PDF.",
            "getting_started": "Comienza en 3 sencillos pasos",
            "step1_title": "1. Escanea un sitio web",
            "step1_desc": "Introduce cualquier URL para realizar un análisis completo de accesibilidad WCAG 2.1 AA con 5 potentes motores de escaneo.",
            "step2_title": "2. Escanea un PDF",
            "step2_desc": "Sube un documento PDF para un análisis de accesibilidad impulsado por IA con tecnología GPT vision.",
            "step3_title": "3. Revisa y corrige",
            "step3_desc": "Obtén recomendaciones accionables para corregir problemas de accesibilidad y seguir tu progreso.",
            "free_credits": "Tus créditos gratuitos",
            "web_credits": "5 créditos de escaneo web por día",
            "pdf_credits": "1 crédito de escaneo PDF por semana",
            "upgrade_note": "¿Necesitas más? Actualiza a Standard o Business para escaneos ilimitados, acceso API e integraciones.",
            "cta": "Inicia tu primer escaneo",
            "help": "¿Necesitas ayuda? Consulta nuestra documentación o contacta con nuestro equipo de soporte."
        },
        "it": {
            "subject": "Benvenuto su LumTrails! 🎉",
            "greeting": f"Benvenuto, {name}!" if name else "Benvenuto!",
            "intro": "Il tuo account è stato verificato e sei pronto per iniziare a migliorare l'accessibilità dei tuoi siti web e documenti PDF.",
            "getting_started": "Inizia in 3 semplici passi",
            "step1_title": "1. Scansiona un sito web",
            "step1_desc": "Inserisci qualsiasi URL per eseguire un'analisi completa di accessibilità WCAG 2.1 AA con 5 potenti motori di scansione.",
            "step2_title": "2. Scansiona un PDF",
            "step2_desc": "Carica un documento PDF per un'analisi di accessibilità basata su IA con tecnologia GPT vision.",
            "step3_title": "3. Esamina e correggi",
            "step3_desc": "Ottieni raccomandazioni azionabili per correggere i problemi di accessibilità e monitorare i tuoi progressi.",
            "free_credits": "I tuoi crediti gratuiti",
            "web_credits": "5 crediti di scansione web al giorno",
            "pdf_credits": "1 credito di scansione PDF a settimana",
            "upgrade_note": "Hai bisogno di più? Passa a Standard o Business per scansioni illimitate, accesso API e integrazioni.",
            "cta": "Inizia la tua prima scansione",
            "help": "Hai bisogno di aiuto? Consulta la nostra documentazione o contatta il nostro team di supporto."
        },
        "pt": {
            "subject": "Bem-vindo ao LumTrails! 🎉",
            "greeting": f"Bem-vindo, {name}!" if name else "Bem-vindo!",
            "intro": "A sua conta foi verificada e está pronto para começar a melhorar a acessibilidade dos seus websites e documentos PDF.",
            "getting_started": "Comece em 3 passos simples",
            "step1_title": "1. Analise um website",
            "step1_desc": "Introduza qualquer URL para realizar uma análise completa de acessibilidade WCAG 2.1 AA com 5 motores de análise poderosos.",
            "step2_title": "2. Analise um PDF",
            "step2_desc": "Carregue um documento PDF para uma análise de acessibilidade alimentada por IA com tecnologia GPT vision.",
            "step3_title": "3. Reveja e corrija",
            "step3_desc": "Obtenha recomendações acionáveis para corrigir problemas de acessibilidade e acompanhar o seu progresso.",
            "free_credits": "Os seus créditos gratuitos",
            "web_credits": "5 créditos de análise web por dia",
            "pdf_credits": "1 crédito de análise PDF por semana",
            "upgrade_note": "Precisa de mais? Atualize para Standard ou Business para análises ilimitadas, acesso à API e integrações.",
            "cta": "Inicie a sua primeira análise",
            "help": "Precisa de ajuda? Consulte a nossa documentação ou contacte a nossa equipa de suporte."
        }
    }
    
    t = templates.get(language, templates["en"])
    
    # Build content using inline styles
    content = f"""
        <h1 style="color: #111827; font-size: 24px; font-weight: 700; margin: 0 0 24px 0;">{t['greeting']}</h1>
        <p style="color: #4b5563; font-size: 16px; margin: 0 0 16px 0;">{t['intro']}</p>
        
        {get_info_box_html(f"<strong>{t['free_credits']}</strong><br/>✓ {t['web_credits']}<br/>✓ {t['pdf_credits']}")}
        
        <h2 style="color: #111827; font-size: 20px; font-weight: 600; margin: 32px 0 16px 0;">{t['getting_started']}</h2>
        
        <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="margin: 16px 0;">
            {get_feature_item_html("🌐", t['step1_title'], t['step1_desc'])}
            {get_feature_item_html("📄", t['step2_title'], t['step2_desc'])}
            {get_feature_item_html("✅", t['step3_title'], t['step3_desc'])}
        </table>
        
        <div style="text-align: center;">
            {get_button_html(t['cta'], f"{FRONTEND_URL}/scan")}
        </div>
        
        <p style="color: #9ca3af; font-size: 14px; margin: 24px 0 8px 0;">{t['upgrade_note']}</p>
        <p style="color: #9ca3af; font-size: 14px; margin: 0;">{t['help']}</p>
    """
    
    return {
        "subject": t["subject"],
        "html_content": get_base_template(content, language)
    }
