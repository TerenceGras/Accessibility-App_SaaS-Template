#!/usr/bin/env python3
"""
LumTrails Pricing Service - Webhook Idempotency

Prevents duplicate webhook event processing using Firestore.
"""
import os
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from google.cloud import firestore

logger = logging.getLogger(__name__)

# CET timezone for EU service
CET = ZoneInfo("Europe/Paris")

# How long to keep processed event records (for cleanup)
EVENT_RETENTION_DAYS = 7


class IdempotencyService:
    """
    Service for ensuring webhook events are processed exactly once.
    
    Stores processed event IDs in Firestore with TTL for automatic cleanup.
    """
    
    def __init__(self):
        """Initialize idempotency service"""
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "")
        self.db = firestore.Client(project=self.project_id)
        self.collection = "webhook_events"
    
    def is_event_processed(self, event_id: str) -> bool:
        """
        Check if an event has already been processed.
        
        Args:
            event_id: Stripe event ID
        
        Returns:
            True if already processed, False otherwise
        """
        try:
            doc = self.db.collection(self.collection).document(event_id).get()
            return doc.exists
        except Exception as e:
            logger.error(f"Error checking if event {event_id} is processed: {e}")
            # In case of error, assume not processed to avoid missing events
            return False
    
    def mark_event_processed(
        self,
        event_id: str,
        event_type: str,
        user_id: str = None,
        details: dict = None
    ):
        """
        Mark an event as processed.
        
        Args:
            event_id: Stripe event ID
            event_type: Type of the event (e.g., 'invoice.payment_succeeded')
            user_id: Associated user ID (optional)
            details: Additional details about processing (optional)
        """
        try:
            now = datetime.now(CET)
            self.db.collection(self.collection).document(event_id).set({
                "event_id": event_id,
                "event_type": event_type,
                "user_id": user_id,
                "processed_at": now,
                "expires_at": now + timedelta(days=EVENT_RETENTION_DAYS),
                "details": details or {}
            })
            logger.info(f"Marked event {event_id} ({event_type}) as processed")
        except Exception as e:
            logger.error(f"Error marking event {event_id} as processed: {e}")
            # Don't raise - we don't want to fail the webhook just because of logging
    
    def cleanup_old_events(self) -> int:
        """
        Clean up old processed events.
        
        Returns:
            Number of events cleaned up
        """
        try:
            now = datetime.now(CET)
            expired_docs = self.db.collection(self.collection)\
                .where("expires_at", "<", now)\
                .stream()
            
            count = 0
            for doc in expired_docs:
                doc.reference.delete()
                count += 1
            
            if count > 0:
                logger.info(f"Cleaned up {count} expired webhook event records")
            
            return count
        except Exception as e:
            logger.error(f"Error cleaning up old events: {e}")
            return 0


# Global idempotency service instance
idempotency_service = IdempotencyService()
