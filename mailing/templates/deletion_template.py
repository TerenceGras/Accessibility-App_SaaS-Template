#!/usr/bin/env python3
"""
LumTrails Mailing Service - Account Deletion Email Templates

Email-client-friendly deletion emails using table-based layout
"""
from .base_template import get_base_template, get_button_html, get_warning_box_html
from config import FRONTEND_URL


def get_deletion_request_email(name: str = "", language: str = "en") -> dict:
    """
    Generate deletion request confirmation email (when user requests account deletion)
    
    Returns:
        Dict with subject and html_content
    """
    templates = {
        "en": {
            "subject": "Account Deletion Request Received",
            "greeting": f"Hello {name}," if name else "Hello,",
            "intro": "We've received your request to delete your LumTrails account.",
            "what_happens": "What happens next?",
            "step1": "Your account will be scheduled for deletion within 24-48 hours.",
            "step2": "All your scan history, saved reports, and personal data will be permanently removed.",
            "step3": "Any active subscription will be cancelled automatically.",
            "step4": "You will receive a final confirmation email once deletion is complete.",
            "change_mind": "Changed your mind?",
            "cancel_note": "If you didn't request this deletion or want to cancel, please log in to your account or contact our support team immediately.",
            "cta": "Log In to Cancel",
            "warning": "⚠️ This action cannot be undone. Once your account is deleted, all data will be permanently lost.",
            "thanks": "We're sorry to see you go. Thank you for using LumTrails."
        },
        "fr": {
            "subject": "Demande de suppression de compte reçue",
            "greeting": f"Bonjour {name}," if name else "Bonjour,",
            "intro": "Nous avons reçu votre demande de suppression de votre compte LumTrails.",
            "what_happens": "Que se passe-t-il ensuite ?",
            "step1": "Votre compte sera programmé pour suppression dans 24-48 heures.",
            "step2": "Tout votre historique d'analyses, vos rapports sauvegardés et vos données personnelles seront définitivement supprimés.",
            "step3": "Tout abonnement actif sera automatiquement annulé.",
            "step4": "Vous recevrez un e-mail de confirmation final une fois la suppression terminée.",
            "change_mind": "Vous avez changé d'avis ?",
            "cancel_note": "Si vous n'avez pas demandé cette suppression ou souhaitez l'annuler, veuillez vous connecter à votre compte ou contacter notre équipe de support immédiatement.",
            "cta": "Se connecter pour annuler",
            "warning": "⚠️ Cette action est irréversible. Une fois votre compte supprimé, toutes les données seront définitivement perdues.",
            "thanks": "Nous sommes désolés de vous voir partir. Merci d'avoir utilisé LumTrails."
        },
        "de": {
            "subject": "Anfrage zur Kontolöschung erhalten",
            "greeting": f"Hallo {name}," if name else "Hallo,",
            "intro": "Wir haben Ihre Anfrage zur Löschung Ihres LumTrails-Kontos erhalten.",
            "what_happens": "Was passiert als nächstes?",
            "step1": "Ihr Konto wird innerhalb von 24-48 Stunden zur Löschung vorgemerkt.",
            "step2": "Ihr gesamter Scan-Verlauf, gespeicherte Berichte und persönliche Daten werden dauerhaft entfernt.",
            "step3": "Aktive Abonnements werden automatisch gekündigt.",
            "step4": "Sie erhalten eine abschließende Bestätigungs-E-Mail, sobald die Löschung abgeschlossen ist.",
            "change_mind": "Haben Sie es sich anders überlegt?",
            "cancel_note": "Wenn Sie diese Löschung nicht angefordert haben oder sie stornieren möchten, melden Sie sich bitte bei Ihrem Konto an oder kontaktieren Sie unser Support-Team sofort.",
            "cta": "Zum Stornieren anmelden",
            "warning": "⚠️ Diese Aktion kann nicht rückgängig gemacht werden. Sobald Ihr Konto gelöscht ist, sind alle Daten dauerhaft verloren.",
            "thanks": "Es tut uns leid, Sie gehen zu sehen. Vielen Dank für die Nutzung von LumTrails."
        },
        "es": {
            "subject": "Solicitud de eliminación de cuenta recibida",
            "greeting": f"Hola {name}," if name else "Hola,",
            "intro": "Hemos recibido tu solicitud para eliminar tu cuenta de LumTrails.",
            "what_happens": "¿Qué sucederá a continuación?",
            "step1": "Tu cuenta será programada para eliminación dentro de 24-48 horas.",
            "step2": "Todo tu historial de escaneos, informes guardados y datos personales serán eliminados permanentemente.",
            "step3": "Cualquier suscripción activa será cancelada automáticamente.",
            "step4": "Recibirás un correo de confirmación final cuando la eliminación esté completa.",
            "change_mind": "¿Has cambiado de opinión?",
            "cancel_note": "Si no solicitaste esta eliminación o deseas cancelarla, por favor inicia sesión en tu cuenta o contacta a nuestro equipo de soporte inmediatamente.",
            "cta": "Iniciar sesión para cancelar",
            "warning": "⚠️ Esta acción no se puede deshacer. Una vez que tu cuenta sea eliminada, todos los datos se perderán permanentemente.",
            "thanks": "Lamentamos verte partir. Gracias por usar LumTrails."
        },
        "it": {
            "subject": "Richiesta di eliminazione account ricevuta",
            "greeting": f"Ciao {name}," if name else "Ciao,",
            "intro": "Abbiamo ricevuto la tua richiesta di eliminazione del tuo account LumTrails.",
            "what_happens": "Cosa succederà dopo?",
            "step1": "Il tuo account sarà programmato per l'eliminazione entro 24-48 ore.",
            "step2": "Tutta la cronologia delle scansioni, i report salvati e i dati personali saranno rimossi permanentemente.",
            "step3": "Eventuali abbonamenti attivi saranno cancellati automaticamente.",
            "step4": "Riceverai un'email di conferma finale quando l'eliminazione sarà completata.",
            "change_mind": "Hai cambiato idea?",
            "cancel_note": "Se non hai richiesto questa eliminazione o vuoi annullarla, accedi al tuo account o contatta il nostro team di supporto immediatamente.",
            "cta": "Accedi per annullare",
            "warning": "⚠️ Questa azione non può essere annullata. Una volta eliminato il tuo account, tutti i dati saranno persi permanentemente.",
            "thanks": "Ci dispiace vederti andare. Grazie per aver usato LumTrails."
        },
        "pt": {
            "subject": "Pedido de eliminação de conta recebido",
            "greeting": f"Olá {name}," if name else "Olá,",
            "intro": "Recebemos o seu pedido para eliminar a sua conta LumTrails.",
            "what_happens": "O que acontece a seguir?",
            "step1": "A sua conta será agendada para eliminação dentro de 24-48 horas.",
            "step2": "Todo o seu histórico de análises, relatórios guardados e dados pessoais serão permanentemente removidos.",
            "step3": "Qualquer subscrição ativa será cancelada automaticamente.",
            "step4": "Receberá um email de confirmação final quando a eliminação estiver concluída.",
            "change_mind": "Mudou de ideias?",
            "cancel_note": "Se não solicitou esta eliminação ou deseja cancelar, por favor inicie sessão na sua conta ou contacte a nossa equipa de suporte imediatamente.",
            "cta": "Iniciar sessão para cancelar",
            "warning": "⚠️ Esta ação não pode ser desfeita. Uma vez eliminada a sua conta, todos os dados serão permanentemente perdidos.",
            "thanks": "Lamentamos vê-lo partir. Obrigado por usar o LumTrails."
        }
    }
    
    t = templates.get(language, templates["en"])
    
    content = f"""
        <h1 style="color: #dc2626; font-size: 24px; font-weight: 700; margin: 0 0 24px 0;">{t['subject']}</h1>
        <p style="color: #4b5563; font-size: 16px; margin: 0 0 8px 0;">{t['greeting']}</p>
        <p style="color: #4b5563; font-size: 16px; margin: 0 0 24px 0;">{t['intro']}</p>
        
        <h2 style="color: #111827; font-size: 20px; font-weight: 600; margin: 0 0 16px 0;">{t['what_happens']}</h2>
        
        <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="margin: 0 0 24px 0;">
            <tr><td style="padding: 8px 0; color: #4b5563;"><span style="color: #6b7280; margin-right: 8px;">1.</span> {t['step1']}</td></tr>
            <tr><td style="padding: 8px 0; color: #4b5563;"><span style="color: #6b7280; margin-right: 8px;">2.</span> {t['step2']}</td></tr>
            <tr><td style="padding: 8px 0; color: #4b5563;"><span style="color: #6b7280; margin-right: 8px;">3.</span> {t['step3']}</td></tr>
            <tr><td style="padding: 8px 0; color: #4b5563;"><span style="color: #6b7280; margin-right: 8px;">4.</span> {t['step4']}</td></tr>
        </table>
        
        {get_warning_box_html(t['warning'])}
        
        <h2 style="color: #111827; font-size: 20px; font-weight: 600; margin: 32px 0 16px 0;">{t['change_mind']}</h2>
        <p style="color: #4b5563; font-size: 16px; margin: 0 0 16px 0;">{t['cancel_note']}</p>
        
        <div style="text-align: center;">
            {get_button_html(t['cta'], f"{FRONTEND_URL}/login", "#6b7280")}
        </div>
        
        <p style="color: #6b7280; font-size: 14px; margin: 24px 0 0 0;">{t['thanks']}</p>
    """
    
    return {
        "subject": t["subject"],
        "html_content": get_base_template(content, language)
    }


def get_account_deleted_email(name: str = "", language: str = "en") -> dict:
    """
    Generate account deleted confirmation email (when deletion is complete)
    
    Returns:
        Dict with subject and html_content
    """
    templates = {
        "en": {
            "subject": "Your LumTrails Account Has Been Deleted",
            "greeting": f"Goodbye {name}," if name else "Goodbye,",
            "intro": "Your LumTrails account has been permanently deleted as requested.",
            "what_deleted": "What has been removed:",
            "item1": "Your account profile and login credentials",
            "item2": "All scan history and saved reports",
            "item3": "Personal data and preferences",
            "item4": "Any active subscriptions (refunds processed if applicable)",
            "come_back": "You're always welcome back!",
            "comeback_note": "If you ever want to use LumTrails again, you can create a new account anytime. We'd love to help you make the web more accessible.",
            "cta": "Create New Account",
            "thanks": "Thank you for being part of the LumTrails community. We wish you all the best!"
        },
        "fr": {
            "subject": "Votre compte LumTrails a été supprimé",
            "greeting": f"Au revoir {name}," if name else "Au revoir,",
            "intro": "Votre compte LumTrails a été définitivement supprimé comme demandé.",
            "what_deleted": "Ce qui a été supprimé :",
            "item1": "Votre profil de compte et vos identifiants de connexion",
            "item2": "Tout l'historique des analyses et les rapports sauvegardés",
            "item3": "Données personnelles et préférences",
            "item4": "Tout abonnement actif (remboursements traités le cas échéant)",
            "come_back": "Vous êtes toujours le bienvenu !",
            "comeback_note": "Si vous souhaitez réutiliser LumTrails, vous pouvez créer un nouveau compte à tout moment. Nous serions ravis de vous aider à rendre le web plus accessible.",
            "cta": "Créer un nouveau compte",
            "thanks": "Merci d'avoir fait partie de la communauté LumTrails. Nous vous souhaitons tout le meilleur !"
        },
        "de": {
            "subject": "Ihr LumTrails-Konto wurde gelöscht",
            "greeting": f"Auf Wiedersehen {name}," if name else "Auf Wiedersehen,",
            "intro": "Ihr LumTrails-Konto wurde wie gewünscht dauerhaft gelöscht.",
            "what_deleted": "Was wurde entfernt:",
            "item1": "Ihr Kontoprofil und Anmeldedaten",
            "item2": "Alle Scan-Verläufe und gespeicherten Berichte",
            "item3": "Persönliche Daten und Einstellungen",
            "item4": "Aktive Abonnements (Rückerstattungen werden ggf. bearbeitet)",
            "come_back": "Sie sind jederzeit willkommen!",
            "comeback_note": "Wenn Sie LumTrails erneut nutzen möchten, können Sie jederzeit ein neues Konto erstellen. Wir würden uns freuen, Ihnen zu helfen, das Web zugänglicher zu machen.",
            "cta": "Neues Konto erstellen",
            "thanks": "Vielen Dank, dass Sie Teil der LumTrails-Community waren. Wir wünschen Ihnen alles Gute!"
        },
        "es": {
            "subject": "Tu cuenta de LumTrails ha sido eliminada",
            "greeting": f"Adiós {name}," if name else "Adiós,",
            "intro": "Tu cuenta de LumTrails ha sido eliminada permanentemente según lo solicitado.",
            "what_deleted": "Lo que se ha eliminado:",
            "item1": "Tu perfil de cuenta y credenciales de inicio de sesión",
            "item2": "Todo el historial de escaneos e informes guardados",
            "item3": "Datos personales y preferencias",
            "item4": "Cualquier suscripción activa (reembolsos procesados si corresponde)",
            "come_back": "¡Siempre eres bienvenido de vuelta!",
            "comeback_note": "Si alguna vez quieres usar LumTrails de nuevo, puedes crear una nueva cuenta en cualquier momento. Nos encantaría ayudarte a hacer la web más accesible.",
            "cta": "Crear nueva cuenta",
            "thanks": "Gracias por ser parte de la comunidad LumTrails. ¡Te deseamos lo mejor!"
        },
        "it": {
            "subject": "Il tuo account LumTrails è stato eliminato",
            "greeting": f"Arrivederci {name}," if name else "Arrivederci,",
            "intro": "Il tuo account LumTrails è stato eliminato permanentemente come richiesto.",
            "what_deleted": "Cosa è stato rimosso:",
            "item1": "Il tuo profilo account e le credenziali di accesso",
            "item2": "Tutta la cronologia delle scansioni e i report salvati",
            "item3": "Dati personali e preferenze",
            "item4": "Eventuali abbonamenti attivi (rimborsi elaborati se applicabile)",
            "come_back": "Sei sempre il benvenuto!",
            "comeback_note": "Se vorrai usare di nuovo LumTrails, potrai creare un nuovo account in qualsiasi momento. Ci farebbe piacere aiutarti a rendere il web più accessibile.",
            "cta": "Crea nuovo account",
            "thanks": "Grazie per essere stato parte della community LumTrails. Ti auguriamo il meglio!"
        },
        "pt": {
            "subject": "A sua conta LumTrails foi eliminada",
            "greeting": f"Adeus {name}," if name else "Adeus,",
            "intro": "A sua conta LumTrails foi permanentemente eliminada conforme solicitado.",
            "what_deleted": "O que foi removido:",
            "item1": "O seu perfil de conta e credenciais de login",
            "item2": "Todo o histórico de análises e relatórios guardados",
            "item3": "Dados pessoais e preferências",
            "item4": "Qualquer subscrição ativa (reembolsos processados se aplicável)",
            "come_back": "É sempre bem-vindo de volta!",
            "comeback_note": "Se algum dia quiser usar o LumTrails novamente, pode criar uma nova conta a qualquer momento. Adoraríamos ajudá-lo a tornar a web mais acessível.",
            "cta": "Criar nova conta",
            "thanks": "Obrigado por fazer parte da comunidade LumTrails. Desejamos-lhe tudo de bom!"
        }
    }
    
    t = templates.get(language, templates["en"])
    
    content = f"""
        <h1 style="color: #111827; font-size: 24px; font-weight: 700; margin: 0 0 24px 0;">{t['subject']}</h1>
        <p style="color: #4b5563; font-size: 16px; margin: 0 0 8px 0;">{t['greeting']}</p>
        <p style="color: #4b5563; font-size: 16px; margin: 0 0 24px 0;">{t['intro']}</p>
        
        <h2 style="color: #111827; font-size: 18px; font-weight: 600; margin: 0 0 16px 0;">{t['what_deleted']}</h2>
        
        <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="margin: 0 0 24px 0;">
            <tr><td style="padding: 8px 0; color: #4b5563;">• {t['item1']}</td></tr>
            <tr><td style="padding: 8px 0; color: #4b5563;">• {t['item2']}</td></tr>
            <tr><td style="padding: 8px 0; color: #4b5563;">• {t['item3']}</td></tr>
            <tr><td style="padding: 8px 0; color: #4b5563;">• {t['item4']}</td></tr>
        </table>
        
        <h2 style="color: #111827; font-size: 20px; font-weight: 600; margin: 32px 0 16px 0;">{t['come_back']}</h2>
        <p style="color: #4b5563; font-size: 16px; margin: 0 0 16px 0;">{t['comeback_note']}</p>
        
        <div style="text-align: center;">
            {get_button_html(t['cta'], f"{FRONTEND_URL}/login")}
        </div>
        
        <p style="color: #6b7280; font-size: 14px; margin: 24px 0 0 0; text-align: center;">{t['thanks']}</p>
    """
    
    return {
        "subject": t["subject"],
        "html_content": get_base_template(content, language)
    }
