#!/usr/bin/env python3
"""
LumTrails Mailing Service - Brevo (SendInBlue) Integration
"""
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from typing import Optional, Dict, Any, List
from config import BREVO_API_KEY, SENDER_EMAIL, SENDER_NAME

logger = logging.getLogger(__name__)

# Thread pool for running sync Brevo SDK calls
_executor = ThreadPoolExecutor(max_workers=10)


class BrevoService:
    """Brevo (SendInBlue) email service integration"""
    
    def __init__(self):
        self.api_key = BREVO_API_KEY
        self._configuration = None
        self._api_instance = None
        
        if self.api_key:
            self._configure()
    
    def _configure(self):
        """Configure Brevo API client"""
        self._configuration = sib_api_v3_sdk.Configuration()
        self._configuration.api_key['api-key'] = self.api_key
        self._api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
            sib_api_v3_sdk.ApiClient(self._configuration)
        )
    
    def is_configured(self) -> bool:
        """Check if Brevo is properly configured"""
        return bool(self.api_key and self._api_instance)
    
    def _send_email_sync(
        self,
        to_email: str,
        to_name: Optional[str],
        subject: str,
        html_content: str,
        reply_to_email: Optional[str] = None,
        reply_to_name: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Synchronous email sending - runs in thread pool"""
        try:
            # Build recipient
            to = [{"email": to_email}]
            if to_name:
                to[0]["name"] = to_name
            
            # Build sender
            sender = {"email": SENDER_EMAIL, "name": SENDER_NAME}
            
            # Build email
            send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
                to=to,
                sender=sender,
                subject=subject,
                html_content=html_content,
                tags=tags or ["lumtrails"]
            )
            
            # Add reply-to if specified
            if reply_to_email:
                send_smtp_email.reply_to = {"email": reply_to_email}
                if reply_to_name:
                    send_smtp_email.reply_to["name"] = reply_to_name
            
            # Send email (sync call)
            response = self._api_instance.send_transac_email(send_smtp_email)
            
            logger.info(f"Email sent successfully to {to_email}, message_id: {response.message_id}")
            return {
                "success": True,
                "message_id": response.message_id
            }
            
        except ApiException as e:
            logger.error(f"Brevo API error sending email to {to_email}: {e}")
            return {
                "success": False,
                "error": f"Failed to send email: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Unexpected error sending email to {to_email}: {e}")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }
    
    def send_email(
        self,
        to_email: str,
        to_name: Optional[str],
        subject: str,
        html_content: str,
        reply_to_email: Optional[str] = None,
        reply_to_name: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Send a transactional email via Brevo (synchronous version for compatibility)
        
        Args:
            to_email: Recipient email address
            to_name: Recipient name (optional)
            subject: Email subject
            html_content: HTML content of the email
            reply_to_email: Reply-to email address (optional)
            reply_to_name: Reply-to name (optional)
            tags: List of tags for tracking (optional)
            
        Returns:
            Dict with success status and message_id or error
        """
        if not self.is_configured():
            logger.error("Brevo API not configured")
            return {"success": False, "error": "Email service not configured"}
        
        return self._send_email_sync(
            to_email=to_email,
            to_name=to_name,
            subject=subject,
            html_content=html_content,
            reply_to_email=reply_to_email,
            reply_to_name=reply_to_name,
            tags=tags
        )
    
    async def send_email_async(
        self,
        to_email: str,
        to_name: Optional[str],
        subject: str,
        html_content: str,
        reply_to_email: Optional[str] = None,
        reply_to_name: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Send a transactional email via Brevo (async version - runs sync call in thread pool)
        
        Args:
            to_email: Recipient email address
            to_name: Recipient name (optional)
            subject: Email subject
            html_content: HTML content of the email
            reply_to_email: Reply-to email address (optional)
            reply_to_name: Reply-to name (optional)
            tags: List of tags for tracking (optional)
            
        Returns:
            Dict with success status and message_id or error
        """
        if not self.is_configured():
            logger.error("Brevo API not configured")
            return {"success": False, "error": "Email service not configured"}
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            _executor,
            lambda: self._send_email_sync(
                to_email=to_email,
                to_name=to_name,
                subject=subject,
                html_content=html_content,
                reply_to_email=reply_to_email,
                reply_to_name=reply_to_name,
                tags=tags
            )
        )
    
    def send_bulk_emails(
        self,
        recipients: List[Dict[str, Any]],
        subject: str,
        html_content_template: str,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Send bulk emails (for newsletter)
        
        Args:
            recipients: List of dicts with email, name, and any personalization params
            subject: Email subject
            html_content_template: HTML template (can include {{name}} for personalization)
            tags: List of tags for tracking
            
        Returns:
            Dict with success count and failed count
        """
        if not self.is_configured():
            logger.error("Brevo API not configured")
            return {"success": False, "sent_count": 0, "failed_count": len(recipients)}
        
        sent_count = 0
        failed_count = 0
        
        for recipient in recipients:
            try:
                email = recipient.get("email")
                name = recipient.get("name", "")
                
                # Personalize content
                personalized_content = html_content_template.replace("{{name}}", name or "there")
                personalized_content = personalized_content.replace("{{email}}", email)
                
                result = self.send_email(
                    to_email=email,
                    to_name=name,
                    subject=subject,
                    html_content=personalized_content,
                    tags=tags or ["newsletter"]
                )
                
                if result.get("success"):
                    sent_count += 1
                else:
                    failed_count += 1
                    logger.warning(f"Failed to send to {email}: {result.get('error')}")
                    
            except Exception as e:
                failed_count += 1
                logger.error(f"Error sending to {recipient.get('email')}: {e}")
        
        return {
            "success": failed_count == 0,
            "sent_count": sent_count,
            "failed_count": failed_count
        }


# Singleton instance
_brevo_service: Optional[BrevoService] = None


def get_brevo_service() -> BrevoService:
    """Get or create Brevo service singleton"""
    global _brevo_service
    if _brevo_service is None:
        _brevo_service = BrevoService()
    return _brevo_service
