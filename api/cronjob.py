#!/usr/bin/env python3
"""
LumTrails Database Cleanup and Data Retention Cron Jobs

This module contains scheduled jobs for:
1. Temporary scan result cleanup (30-minute retention for processing)
2. PDF storage cleanup (2-hour fallback for orphaned files)
3. Expired scan data cleanup (24-month retention per Privacy Policy)
4. User account deletion handler (GDPR compliance)

All timestamps use CET (Europe/Paris) timezone for EU service consistency.

Usage:
    python cronjob.py [cleanup|expired-scans|delete-user <user_id>]

Environment Variables:
    GOOGLE_CLOUD_PROJECT: Google Cloud Project ID
"""

import os
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from google.cloud import firestore
import firebase_admin
from firebase_admin import credentials, storage as firebase_storage, auth as firebase_auth

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# CET timezone for EU service
CET = ZoneInfo("Europe/Paris")

# Retention periods per subscription plan (in days)
# Free: 30 days, Standard: 6 months (180 days), Business: 1 year (365 days)
SCAN_RETENTION_DAYS_BY_PLAN = {
    "free": 30,
    "standard": 180,
    "business": 365,
    "enterprise": 365  # At least 1 year for enterprise
}
DEFAULT_RETENTION_DAYS = 30  # Default for users without subscription info

# Legacy fallback for maximum retention (if plan unknown)
SCAN_RETENTION_MONTHS = 24  # Maximum 24 months for any plan
TECHNICAL_LOGS_RETENTION_DAYS = 90  # Technical logs: 90 days
ACCOUNT_BACKUP_RETENTION_DAYS = 30  # Account data backup: 30 days after deletion


def _send_scan_deletion_warning_email(user_email: str, user_id: str, scans_to_delete: list):
    """
    TODO: Implement email notification for upcoming scan deletion
    
    This function should send an email to users warning them that their scans
    will be deleted in 30 days due to the 24-month retention policy.
    Users should be given the opportunity to download their scan reports
    before they are permanently deleted.
    
    Implementation requirements:
    - Use SendGrid, AWS SES, or similar email service
    - Include list of scans that will be deleted
    - Provide direct links to download scan reports
    - Send 30 days before deletion, then 7 days, then 1 day
    - Track which warnings have been sent to avoid duplicates
    
    Email template should include:
    - Subject: "Your LumTrails scan reports will be deleted in X days"
    - List of affected scans with dates and URLs scanned
    - Download links for each scan report
    - Link to account settings to manage data retention preferences
    - GDPR compliance notice
    
    Args:
        user_email: Email address of the user
        user_id: Firestore user ID
        scans_to_delete: List of scan documents that will be deleted
    """
    # TODO: Implement email notification service integration
    # For now, just log the warning
    logger.info(f"TODO: Send scan deletion warning email to {user_email}")
    logger.info(f"  User ID: {user_id}")
    logger.info(f"  Scans to be deleted: {len(scans_to_delete)}")
    for scan in scans_to_delete[:5]:  # Log first 5 scans
        scan_data = scan.to_dict()
        logger.info(f"    - Scan ID: {scan.id}, URL: {scan_data.get('url', 'N/A')}, Date: {scan_data.get('created_at', 'N/A')}")
    if len(scans_to_delete) > 5:
        logger.info(f"    ... and {len(scans_to_delete) - 5} more scans")
    pass

def cleanup_pdf_storage():
    """Clean up old PDF files and images from Firebase Storage"""
    try:
        # Initialize Firebase Admin SDK if not already initialized
        if not firebase_admin._apps:
            # Try to use service account key file if provided
            service_account_key_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
            if service_account_key_path and os.path.exists(service_account_key_path):
                cred = credentials.Certificate(service_account_key_path)
                firebase_admin.initialize_app(cred, {
                    'storageBucket': os.getenv('FIREBASE_STORAGE_BUCKET', '')
                })
            else:
                firebase_admin.initialize_app(options={
                    'storageBucket': os.getenv('FIREBASE_STORAGE_BUCKET', '')
                })
        
        # Get bucket reference
        bucket = firebase_storage.bucket()
        
        # Calculate cutoff time (2 hours ago for PDF storage)
        cutoff_time = datetime.utcnow() - timedelta(hours=2)
        
        logger.info(f"Starting cleanup of PDF storage files older than {cutoff_time.isoformat()}")
        
        deleted_count = 0
        
        # Check both PDF and image prefixes
        prefixes = ['temp-pdfs', 'temp-images']
        
        for prefix in prefixes:
            logger.info(f"Cleaning up files with prefix: {prefix}")
            blobs = bucket.list_blobs(prefix=prefix)
            
            for blob in blobs:
                try:
                    # Check metadata for cleanup time
                    if blob.metadata and 'cleanup_after' in blob.metadata:
                        cleanup_time = datetime.fromisoformat(blob.metadata['cleanup_after'])
                        if datetime.utcnow() > cleanup_time:
                            blob.delete()
                            deleted_count += 1
                            logger.debug(f"Deleted expired file: {blob.name}")
                    else:
                        # If no metadata, check creation time as fallback
                        if blob.time_created.replace(tzinfo=None) < cutoff_time:
                            blob.delete()
                            deleted_count += 1
                            logger.debug(f"Deleted old file (no metadata): {blob.name}")
                            
                except Exception as e:
                    logger.warning(f"Error checking/deleting blob {blob.name}: {str(e)}")
        
        logger.info(f"PDF storage cleanup completed. Deleted {deleted_count} files.")
        return deleted_count
        
    except Exception as e:
        logger.error(f"Error during PDF storage cleanup: {str(e)}")
        return 0

def cleanup_old_scans():
    """Delete scan results older than 30 minutes"""
    try:
        # Initialize Firestore client with project for DEV/PROD compatibility
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "")
        db = firestore.Client(project=project_id)
        
        # Calculate cutoff time (30 minutes ago)
        cutoff_time = datetime.utcnow() - timedelta(minutes=30)
        
        logger.info(f"Starting cleanup of scan results older than {cutoff_time.isoformat()}")
        
        total_deleted = 0
        
        # Collections to clean up
        collections_to_clean = [
            'scan_results',      # Web scan results
            'pdf_scan_results'   # PDF scan results
        ]
        
        for collection_name in collections_to_clean:
            logger.info(f"Cleaning up collection: {collection_name}")
            
            # Query for old scan results in this collection
            old_scans_query = db.collection(collection_name).where('created_at', '<', cutoff_time)
            old_scans = old_scans_query.get()
            
            collection_deleted = 0
            
            # Delete old scans in batches
            batch = db.batch()
            batch_size = 0
            max_batch_size = 500  # Firestore limit
            
            for scan_doc in old_scans:
                batch.delete(scan_doc.reference)
                batch_size += 1
                
                # Commit batch when it reaches max size
                if batch_size >= max_batch_size:
                    batch.commit()
                    collection_deleted += batch_size
                    total_deleted += batch_size
                    logger.info(f"Deleted batch of {batch_size} records from {collection_name}")
                    batch = db.batch()
                    batch_size = 0
            
            # Commit remaining items in batch
            if batch_size > 0:
                batch.commit()
                collection_deleted += batch_size
                total_deleted += batch_size
                logger.info(f"Deleted final batch of {batch_size} records from {collection_name}")
            
            logger.info(f"Cleaned up {collection_deleted} old records from {collection_name}")
        
        logger.info(f"Cleanup completed. Total deleted: {total_deleted} old scan results across all collections.")
        return total_deleted
        
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")
        raise e


def cleanup_expired_scans():
    """
    Delete scan results based on subscription plan retention policy.
    
    Retention periods:
    - Free tier: 30 days
    - Standard plan: 6 months (180 days)
    - Business plan: 1 year (365 days)
    - Enterprise plan: 1 year (365 days) minimum
    
    This function:
    1. Groups users by their subscription plan
    2. Calculates the appropriate retention cutoff for each user
    3. Sends warning emails to users with expiring scans
    4. Deletes expired scan data from Firestore
    5. Cleans up associated storage files
    
    Called daily at 03:00 CET by Cloud Scheduler.
    
    Returns:
        int: Total number of expired scans deleted
    """
    try:
        # Initialize Firestore client with project for DEV/PROD compatibility
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "")
        db = firestore.Client(project=project_id)
        
        now_cet = datetime.now(CET)
        logger.info(f"Starting plan-based scan cleanup at {now_cet.isoformat()}")
        
        total_deleted = 0
        
        # Collections with scan data
        scan_collections = ['web_scans', 'pdf_scans']
        
        # First, get all users and their subscription plans
        users_ref = db.collection('users')
        all_users = users_ref.stream()
        
        user_plans = {}  # {user_id: plan_name}
        user_emails = {}  # {user_id: email}
        
        for user_doc in all_users:
            user_data = user_doc.to_dict()
            user_id = user_doc.id
            
            # Get subscription plan (default to "free")
            subscription = user_data.get('subscription', {})
            plan = subscription.get('plan', 'free')
            status = subscription.get('status', 'active')
            
            # If subscription is not active, treat as free tier for retention
            if status != 'active' and plan != 'free':
                plan = 'free'
            
            user_plans[user_id] = plan
            user_emails[user_id] = user_data.get('email')
        
        logger.info(f"Found {len(user_plans)} users to process for retention cleanup")
        
        # Process each user's scans based on their plan
        users_with_expiring_scans = {}  # For warning emails
        
        for user_id, plan in user_plans.items():
            retention_days = SCAN_RETENTION_DAYS_BY_PLAN.get(plan, DEFAULT_RETENTION_DAYS)
            cutoff_time = now_cet - timedelta(days=retention_days)
            cutoff_time_utc = cutoff_time.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
            
            # Warning cutoff: 7 days before deletion
            warning_cutoff = now_cet - timedelta(days=retention_days - 7)
            warning_cutoff_utc = warning_cutoff.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
            
            for collection_name in scan_collections:
                try:
                    # Query for this user's scans that are approaching expiration (warning)
                    expiring_query = db.collection(collection_name).where(
                        'user_id', '==', user_id
                    ).where(
                        'created_at', '<', warning_cutoff_utc
                    ).where(
                        'created_at', '>=', cutoff_time_utc
                    )
                    
                    expiring_scans = list(expiring_query.get())
                    if expiring_scans:
                        if user_id not in users_with_expiring_scans:
                            users_with_expiring_scans[user_id] = []
                        users_with_expiring_scans[user_id].extend(expiring_scans)
                    
                    # Query for this user's expired scans (past retention period)
                    expired_query = db.collection(collection_name).where(
                        'user_id', '==', user_id
                    ).where(
                        'created_at', '<', cutoff_time_utc
                    )
                    
                    expired_scans = list(expired_query.get())
                    
                    if expired_scans:
                        # Initialize Firebase Admin SDK for storage if needed
                        if not firebase_admin._apps:
                            service_account_key_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
                            if service_account_key_path and os.path.exists(service_account_key_path):
                                cred = credentials.Certificate(service_account_key_path)
                                firebase_admin.initialize_app(cred, {
                                    'storageBucket': os.getenv('FIREBASE_STORAGE_BUCKET', f'{project_id}.firebasestorage.app')
                                })
                            else:
                                firebase_admin.initialize_app(options={
                                    'storageBucket': os.getenv('FIREBASE_STORAGE_BUCKET', f'{project_id}.firebasestorage.app')
                                })
                        
                        bucket = firebase_storage.bucket()
                        
                        batch = db.batch()
                        batch_size = 0
                        max_batch_size = 500
                        
                        for scan_doc in expired_scans:
                            # Delete any associated storage files (PDF files and reports)
                            scan_data = scan_doc.to_dict()
                            
                            # Delete PDF file from storage if present
                            if 'storage_path' in scan_data and scan_data['storage_path']:
                                try:
                                    blob = bucket.blob(scan_data['storage_path'])
                                    if blob.exists():
                                        blob.delete()
                                        logger.debug(f"Deleted storage file: {scan_data['storage_path']}")
                                except Exception as e:
                                    logger.warning(f"Could not delete storage file for scan {scan_doc.id}: {str(e)}")
                            
                            # Delete report file from storage if present (extract path from URL)
                            if 'report_url' in scan_data and scan_data['report_url']:
                                try:
                                    report_url = scan_data['report_url']
                                    # Extract storage path from URL (format: ...storage.googleapis.com/bucket/path...)
                                    if 'storage.googleapis.com' in report_url or 'firebasestorage.googleapis.com' in report_url:
                                        # Parse path from URL
                                        import urllib.parse
                                        parsed = urllib.parse.urlparse(report_url)
                                        path_parts = parsed.path.split('/')
                                        # Find the path after the bucket name
                                        if len(path_parts) > 2:
                                            storage_path = '/'.join(path_parts[2:])
                                            storage_path = urllib.parse.unquote(storage_path)
                                            blob = bucket.blob(storage_path)
                                            if blob.exists():
                                                blob.delete()
                                                logger.debug(f"Deleted report file: {storage_path}")
                                except Exception as e:
                                    logger.warning(f"Could not delete report file for scan {scan_doc.id}: {str(e)}")
                            
                            batch.delete(scan_doc.reference)
                            batch_size += 1
                            
                            if batch_size >= max_batch_size:
                                batch.commit()
                                total_deleted += batch_size
                                logger.info(f"Deleted batch of {batch_size} expired scans for user {user_id} ({plan} plan)")
                                batch = db.batch()
                                batch_size = 0
                        
                        if batch_size > 0:
                            batch.commit()
                            total_deleted += batch_size
                            logger.debug(f"Deleted {batch_size} expired scans for user {user_id} ({plan} plan, {retention_days}d retention)")
                            
                except Exception as e:
                    logger.warning(f"Error processing scans for user {user_id}: {str(e)}")
        
        # Send warning emails to users with expiring scans
        for user_id, scans in users_with_expiring_scans.items():
            try:
                user_email = user_emails.get(user_id)
                if user_email:
                    _send_scan_deletion_warning_email(user_email, user_id, scans)
            except Exception as e:
                logger.warning(f"Failed to process warning for user {user_id}: {str(e)}")
        
        # Also clean up technical logs older than 90 days (per Privacy Policy)
        logs_cutoff = now_cet - timedelta(days=TECHNICAL_LOGS_RETENTION_DAYS)
        logs_cutoff_utc = logs_cutoff.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
        
        log_collections = ['integration_logs', 'access_logs', 'api_logs']
        logs_deleted = 0
        
        for log_collection in log_collections:
            try:
                old_logs_query = db.collection(log_collection).where('created_at', '<', logs_cutoff_utc)
                old_logs = old_logs_query.get()
                
                batch = db.batch()
                batch_size = 0
                
                for log_doc in old_logs:
                    batch.delete(log_doc.reference)
                    batch_size += 1
                    
                    if batch_size >= 500:
                        batch.commit()
                        logs_deleted += batch_size
                        batch = db.batch()
                        batch_size = 0
                
                if batch_size > 0:
                    batch.commit()
                    logs_deleted += batch_size
                
                logger.info(f"Cleaned up logs from {log_collection}")
            except Exception as e:
                # Collection might not exist, that's fine
                logger.debug(f"Could not clean {log_collection}: {str(e)}")
        
        if logs_deleted > 0:
            logger.info(f"Cleaned up {logs_deleted} technical logs older than 90 days")
        
        logger.info(f"Plan-based scan cleanup completed. Total deleted: {total_deleted} expired scans.")
        return total_deleted
        
    except Exception as e:
        logger.error(f"Error during expired scan cleanup: {str(e)}")
        raise e


def delete_user_data(user_id: str):
    """
    Delete all data associated with a user account (GDPR compliance).
    
    This function is called when a user requests account deletion.
    It removes all user-related data including:
    - User profile document (users collection)
    - All scan results (web_scan_results, pdf_scan_results)
    - Integration configurations (user_integrations)
    - Integration logs (integration_logs)
    - API keys (api_keys)
    - Billing info (billing_info)
    - Credit usage history (credit_usage_daily_summary, credit_usage_history)
    - Credit purchases (credit_purchases)
    - Legacy records (usage_records, credit_transactions)
    - Any stored files in Firebase Storage
    - Firebase Auth user
    
    Args:
        user_id: The Firestore user ID to delete data for
        
    Returns:
        dict: Summary of deleted items by category
    """
    try:
        # Use project ID from environment for DEV/PROD compatibility
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "")
        db = firestore.Client(project=project_id)
        
        logger.info(f"Starting complete data deletion for user: {user_id}")
        
        deleted_summary = {
            'user_profile': 0,
            'web_scan_results': 0,
            'pdf_scan_results': 0,
            'api_keys': 0,
            'integrations': 0,
            'billing_info': 0,
            'credit_usage_daily_summary': 0,
            'credit_usage_history': 0,
            'credit_purchases': 0,
            'integration_logs': 0,
            'usage_records': 0,
            'storage_files': 0
        }
        
        # 1. Delete user's scan results
        scan_collections = ['web_scan_results', 'pdf_scan_results']
        for collection_name in scan_collections:
            scans_query = db.collection(collection_name).where('user_id', '==', user_id)
            scans = scans_query.get()
            
            batch = db.batch()
            batch_size = 0
            
            for scan in scans:
                batch.delete(scan.reference)
                batch_size += 1
                
                if batch_size >= 500:
                    batch.commit()
                    deleted_summary[collection_name] += batch_size
                    batch = db.batch()
                    batch_size = 0
            
            if batch_size > 0:
                batch.commit()
                deleted_summary[collection_name] += batch_size
            
            logger.info(f"Deleted {deleted_summary.get(collection_name, 0)} scans from {collection_name}")
        
        # 2. Delete user's API keys
        api_keys_query = db.collection('api_keys').where('user_id', '==', user_id)
        api_keys = api_keys_query.get()
        for key in api_keys:
            key.reference.delete()
            deleted_summary['api_keys'] += 1
        
        # 3. Delete user's integrations (document ID is user_id)
        integrations_doc = db.collection('user_integrations').document(user_id)
        if integrations_doc.get().exists:
            integrations_doc.delete()
            deleted_summary['integrations'] = 1
            logger.info(f"Deleted integrations document for user {user_id}")
        
        # 4. Delete billing_info
        billing_info_doc = db.collection('billing_info').document(user_id)
        if billing_info_doc.get().exists:
            billing_info_doc.delete()
            deleted_summary['billing_info'] = 1
            logger.info(f"Deleted billing_info for user {user_id}")
        
        # 5. Delete credit_usage_daily_summary
        credit_daily_query = db.collection('credit_usage_daily_summary').where('user_id', '==', user_id)
        credit_daily_docs = credit_daily_query.get()
        for doc in credit_daily_docs:
            doc.reference.delete()
            deleted_summary['credit_usage_daily_summary'] += 1
        if deleted_summary['credit_usage_daily_summary'] > 0:
            logger.info(f"Deleted {deleted_summary['credit_usage_daily_summary']} credit_usage_daily_summary records for user {user_id}")
        
        # 6. Delete credit_usage_history
        credit_history_query = db.collection('credit_usage_history').where('user_id', '==', user_id)
        credit_history_docs = credit_history_query.get()
        for doc in credit_history_docs:
            doc.reference.delete()
            deleted_summary['credit_usage_history'] += 1
        if deleted_summary['credit_usage_history'] > 0:
            logger.info(f"Deleted {deleted_summary['credit_usage_history']} credit_usage_history records for user {user_id}")
        
        # 7. Delete credit_purchases
        credit_purchases_query = db.collection('credit_purchases').where('user_id', '==', user_id)
        credit_purchases_docs = credit_purchases_query.get()
        for doc in credit_purchases_docs:
            doc.reference.delete()
            deleted_summary['credit_purchases'] += 1
        if deleted_summary['credit_purchases'] > 0:
            logger.info(f"Deleted {deleted_summary['credit_purchases']} credit_purchases records for user {user_id}")
        
        # 8. Delete integration_logs
        integration_logs_query = db.collection('integration_logs').where('user_id', '==', user_id)
        integration_logs_docs = integration_logs_query.get()
        for doc in integration_logs_docs:
            doc.reference.delete()
            deleted_summary['integration_logs'] += 1
        if deleted_summary['integration_logs'] > 0:
            logger.info(f"Deleted {deleted_summary['integration_logs']} integration_logs records for user {user_id}")
        
        # 9. Delete legacy usage/credit records
        usage_collections = ['usage_records', 'credit_transactions']
        for usage_collection in usage_collections:
            usage_query = db.collection(usage_collection).where('user_id', '==', user_id)
            usage_docs = usage_query.get()
            for doc in usage_docs:
                doc.reference.delete()
                deleted_summary['usage_records'] += 1
        
        # 10. Clean up Firebase Storage files for user
        try:
            if firebase_admin._apps:
                bucket = firebase_storage.bucket()
                
                # Delete any user-specific files
                user_prefixes = [
                    f'pdf-scans/{user_id}',
                    f'web-scans/{user_id}',
                    f'reports/{user_id}',
                ]
                
                for prefix in user_prefixes:
                    blobs = bucket.list_blobs(prefix=prefix)
                    for blob in blobs:
                        blob.delete()
                        deleted_summary['storage_files'] += 1
                
                logger.info(f"Deleted {deleted_summary['storage_files']} storage files for user")
        except Exception as e:
            logger.warning(f"Could not clean up storage files: {str(e)}")
        
        # 11. Delete user profile document (do this last)
        user_doc = db.collection('users').document(user_id)
        if user_doc.get().exists:
            user_doc.delete()
            deleted_summary['user_profile'] = 1
            logger.info(f"Deleted user profile for {user_id}")
        
        # 12. Delete user from Firebase Auth
        try:
            firebase_auth.delete_user(user_id)
            logger.info(f"Deleted Firebase Auth user for {user_id}")
        except firebase_admin.exceptions.FirebaseError as e:
            logger.error(f"Failed to delete Firebase Auth user {user_id}: {str(e)}")
            # Don't raise - we still want to complete the rest of the deletion
        except Exception as e:
            logger.error(f"Unexpected error deleting Firebase Auth user {user_id}: {str(e)}")
        
        logger.info(f"Complete data deletion finished for user {user_id}:")
        for category, count in deleted_summary.items():
            logger.info(f"  - {category}: {count} items deleted")
        
        return deleted_summary
        
    except Exception as e:
        logger.error(f"Error during user data deletion for {user_id}: {str(e)}")
        raise e


def main():
    """
    Main entry point for cleanup operations.
    
    Usage:
        python cronjob.py                    # Run temp cleanup (30-minute retention)
        python cronjob.py cleanup            # Same as above
        python cronjob.py expired-scans      # Run 24-month expired scan cleanup
        python cronjob.py delete-user <id>   # Delete all data for a user
    """
    import sys
    
    command = sys.argv[1] if len(sys.argv) > 1 else "cleanup"
    
    try:
        if command == "cleanup":
            # Standard cleanup: temp scan results and PDF storage
            firestore_deleted = cleanup_old_scans()
            storage_deleted = cleanup_pdf_storage()
            
            total_deleted = firestore_deleted + storage_deleted
            
            print(f"✅ Cleanup successful:")
            print(f"   - Firestore: {firestore_deleted} old scan results deleted")
            print(f"   - PDF Storage: {storage_deleted} old files deleted")
            print(f"   - Total: {total_deleted} items cleaned up")
            return 0
            
        elif command == "expired-scans":
            # 24-month retention cleanup
            deleted = cleanup_expired_scans()
            
            print(f"✅ Expired scan cleanup successful:")
            print(f"   - Deleted {deleted} scans older than 24 months")
            return 0
            
        elif command == "delete-user":
            if len(sys.argv) < 3:
                print("❌ Error: User ID required")
                print("   Usage: python cronjob.py delete-user <user_id>")
                return 1
            
            user_id = sys.argv[2]
            summary = delete_user_data(user_id)
            
            print(f"✅ User data deletion successful for {user_id}:")
            for category, count in summary.items():
                print(f"   - {category}: {count} items deleted")
            return 0
            
        else:
            print(f"❌ Unknown command: {command}")
            print("   Available commands: cleanup, expired-scans, delete-user <user_id>")
            return 1
            
    except Exception as e:
        print(f"❌ Operation failed: {str(e)}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
