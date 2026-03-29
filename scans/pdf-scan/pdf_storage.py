"""
PDF Storage Management for LumTrails PDF Scanner
=================================================

This module handles temporary storage of PDF files and their extracted page images
in Firebase Storage for processing by the GPT-5 Vision API.

Features:
- Temporary PDF file storage in Firebase Storage
- PDF to image conversion with optimal resolution for OCR/AI analysis
- Temporary image storage with automatic cleanup
- A4 format optimization for document analysis
- Batch management for large PDF files

Storage Strategy:
- PDFs stored temporarily in Firebase Storage bucket
- Images extracted and stored with organized naming convention
- All temporary files automatically cleaned up after scan completion
- Handles large PDF files efficiently
"""

import logging
import tempfile
import os
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import asyncio
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import io

# CET timezone for EU service - all dates stored in CET
CET = ZoneInfo("Europe/Paris")
import base64

logger = logging.getLogger(__name__)

# PDF processing
try:
    from pdf2image import convert_from_path
    from PIL import Image
    import fitz  # PyMuPDF for PDF dimension extraction
    PDF_PROCESSING_AVAILABLE = True
except ImportError as e:
    logger.warning(f"PDF processing dependencies not available: {e}")
    PDF_PROCESSING_AVAILABLE = False
    # Create dummy classes to prevent import errors
    class Image:
        class Image:
            pass
    convert_from_path = None
    fitz = None

# Firebase Storage
try:
    import firebase_admin
    from firebase_admin import credentials, storage as firebase_storage
    FIREBASE_STORAGE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Firebase Storage dependencies not available: {e}")
    FIREBASE_STORAGE_AVAILABLE = False
    firebase_admin = None
    firebase_storage = None

class PDFStorageManager:
    """Manages temporary storage of PDF files and extracted images in Firebase Storage"""
    
    def __init__(self):
        """Initialize the PDF storage manager"""
        self.bucket = None
        self.bucket_name = None
        
        # Configuration for document processing
        self.target_dpi = 200  # Good balance for OCR and file size
        self.pdf_standard_dpi = 72  # PDF standard points per inch
        
        # Hard limits for GPT-5 Vision API (theoretical maximum before downsampling)
        self.MAX_IMAGE_WIDTH = 2048
        self.MAX_IMAGE_HEIGHT = 2048
        
        # Dynamic dimensions (will be calculated from actual PDF)
        self.max_width = None
        self.max_height = None
        
        # Storage organization
        self.pdf_prefix = "temp-pdfs"
        self.images_prefix = "temp-images"
        
        # Cleanup settings
        self.cleanup_after_hours = 2  # Clean up files older than 2 hours
        
        if FIREBASE_STORAGE_AVAILABLE:
            try:
                from google.cloud import secretmanager
                import json
                
                # Initialize Firebase Admin SDK if not already initialized
                if not firebase_admin._apps:
                    # Try to fetch service account key from Secret Manager
                    try:
                        logger.info("Fetching service account key from Secret Manager...")
                        secret_client = secretmanager.SecretManagerServiceClient()
                        project_id = os.getenv('GOOGLE_CLOUD_PROJECT', '')
                        secret_id = os.getenv('FIREBASE_STORAGE_SA_SECRET_NAME', 'firebase-storage-private-key')
                        secret_name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
                        response = secret_client.access_secret_version(request={"name": secret_name})
                        secret_data = response.payload.data.decode('UTF-8')
                        service_account_info = json.loads(secret_data)
                        
                        logger.info("Successfully loaded service account key from Secret Manager")
                        cred = credentials.Certificate(service_account_info)
                        firebase_admin.initialize_app(cred, {
                            'storageBucket': os.getenv('FIREBASE_STORAGE_BUCKET', '')
                        })
                        logger.info("Firebase Admin SDK initialized with service account credentials from Secret Manager")
                    except Exception as secret_error:
                        logger.warning(f"Could not load service account key from Secret Manager: {secret_error}")
                        logger.info("Falling back to default credentials")
                        firebase_admin.initialize_app(options={
                            'storageBucket': os.getenv('FIREBASE_STORAGE_BUCKET', '')
                        })
                        logger.info("Firebase Admin SDK initialized with default credentials")
                
                # Get bucket reference - explicitly specify bucket name
                bucket_name = os.getenv('FIREBASE_STORAGE_BUCKET', '')
                self.bucket = firebase_storage.bucket(bucket_name)
                self.bucket_name = self.bucket.name
                logger.info(f"Connected to Firebase Storage bucket: {self.bucket_name}")
                
            except Exception as e:
                logger.warning(f"Failed to initialize Firebase Storage: {e}")
                self.bucket = None
        else:
            logger.warning("Firebase Storage not available - file operations will fail")
    
    async def store_pdf_temporarily(self, file_content: bytes, file_name: str, task_id: str) -> str:
        """
        Store PDF file temporarily in Firebase Storage
        
        Args:
            file_content: The PDF file content as bytes
            file_name: Original filename
            task_id: Unique task identifier
            
        Returns:
            Storage path for the uploaded PDF
        """
        try:
            if not self.bucket:
                raise Exception("Firebase Storage bucket not initialized")
            
            # Create unique storage path
            storage_path = f"{self.pdf_prefix}/{task_id}/{file_name}"
            blob = self.bucket.blob(storage_path)
            
            # Set metadata for cleanup
            blob.metadata = {
                'task_id': task_id,
                'original_filename': file_name,
                'upload_time': datetime.now(CET).isoformat(),
                'file_type': 'pdf',
                'cleanup_after': (datetime.now(CET) + timedelta(hours=self.cleanup_after_hours)).isoformat()
            }
            
            # Upload the PDF file
            blob.upload_from_string(file_content, content_type='application/pdf')
            
            logger.info(f"PDF uploaded to Firebase Storage: {storage_path}")
            return storage_path
            
        except Exception as e:
            logger.error(f"Failed to store PDF in Firebase Storage: {str(e)}")
            raise
    
    def _extract_pdf_dimensions(self, pdf_path: str) -> Tuple[int, int]:
        """
        Extract dimensions from the first page of the PDF
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Tuple of (target_width, target_height) at target DPI
        """
        try:
            # Open PDF document
            pdf_document = fitz.open(pdf_path)
            
            # Get first page
            first_page = pdf_document[0]
            first_page_rect = first_page.rect
            
            # Extract dimensions in points
            width_pts = first_page_rect.width
            height_pts = first_page_rect.height
            
            # Calculate zoom factor for target DPI
            zoom_factor = self.target_dpi / self.pdf_standard_dpi
            
            # Calculate target dimensions
            target_width = int(width_pts * zoom_factor)
            target_height = int(height_pts * zoom_factor)
            
            # Apply hard limits while preserving aspect ratio
            if target_width > self.MAX_IMAGE_WIDTH or target_height > self.MAX_IMAGE_HEIGHT:
                # Calculate scaling factor to fit within limits
                width_scale = self.MAX_IMAGE_WIDTH / target_width
                height_scale = self.MAX_IMAGE_HEIGHT / target_height
                scale_factor = min(width_scale, height_scale)
                
                # Apply scaling
                original_width, original_height = target_width, target_height
                target_width = int(target_width * scale_factor)
                target_height = int(target_height * scale_factor)
                
                logger.info(f"Scaled down from {original_width}x{original_height} to {target_width}x{target_height} to fit within {self.MAX_IMAGE_WIDTH}x{self.MAX_IMAGE_HEIGHT} limit")
            
            # Close PDF document
            pdf_document.close()
            
            logger.info(f"PDF dimensions: {width_pts:.1f}x{height_pts:.1f} pts -> {target_width}x{target_height} px at {self.target_dpi} DPI")
            
            return target_width, target_height
            
        except Exception as e:
            logger.error(f"Failed to extract PDF dimensions: {str(e)}")
            # Fallback to A4 dimensions if extraction fails
            fallback_width = int(8.27 * self.target_dpi)  # A4 width at target DPI
            fallback_height = int(11.69 * self.target_dpi)  # A4 height at target DPI
            
            # Apply hard limits to fallback dimensions as well
            if fallback_width > self.MAX_IMAGE_WIDTH or fallback_height > self.MAX_IMAGE_HEIGHT:
                width_scale = self.MAX_IMAGE_WIDTH / fallback_width
                height_scale = self.MAX_IMAGE_HEIGHT / fallback_height
                scale_factor = min(width_scale, height_scale)
                
                original_width, original_height = fallback_width, fallback_height
                fallback_width = int(fallback_width * scale_factor)
                fallback_height = int(fallback_height * scale_factor)
                
                logger.warning(f"Scaled fallback A4 dimensions from {original_width}x{original_height} to {fallback_width}x{fallback_height}")
            
            logger.warning(f"Using fallback A4 dimensions: {fallback_width}x{fallback_height}")
            return fallback_width, fallback_height
    
    async def convert_pdf_to_images(self, pdf_storage_path: str, task_id: str) -> List[str]:
        """
        Convert PDF to images and store them in Firebase Storage
        
        Args:
            pdf_storage_path: Path to PDF in Firebase Storage
            task_id: Unique task identifier
            
        Returns:
            List of storage paths for the extracted images
        """
        try:
            if not self.bucket:
                raise Exception("Firebase Storage bucket not initialized")
            
            # Download PDF to temporary local file for processing
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
                blob = self.bucket.blob(pdf_storage_path)
                blob.download_to_filename(temp_pdf.name)
                temp_pdf_path = temp_pdf.name
            
            try:
                # Extract PDF dimensions for optimal conversion
                self.max_width, self.max_height = self._extract_pdf_dimensions(temp_pdf_path)
                
                # Convert PDF to images
                images = convert_from_path(
                    temp_pdf_path,
                    dpi=self.target_dpi,
                    fmt='RGB',
                    first_page=1,
                    last_page=None,  # Convert all pages
                    poppler_path=None  # Use system poppler
                )
                
                logger.info(f"Converted PDF to {len(images)} images at {self.target_dpi} DPI")
                
                # Store each image in Firebase Storage with proper numbering (1 to N)
                image_paths = []
                total_pages = len(images)
                
                for page_num, image in enumerate(images, 1):
                    image_path = await self._store_image(image, task_id, page_num, total_pages)
                    if image_path:
                        image_paths.append(image_path)
                
                logger.info(f"Stored {len(image_paths)} images in Firebase Storage")
                return image_paths
                
            finally:
                # Clean up temporary PDF file
                try:
                    os.unlink(temp_pdf_path)
                except Exception as e:
                    logger.warning(f"Failed to clean up temporary PDF: {str(e)}")
            
        except Exception as e:
            logger.error(f"Failed to convert PDF to images: {str(e)}")
            raise
    
    async def _store_image(self, image: Image.Image, task_id: str, page_num: int, total_pages: int) -> Optional[str]:
        """
        Store a single image in Firebase Storage
        
        Args:
            image: PIL Image object
            task_id: Unique task identifier
            page_num: Page number (1-indexed)
            total_pages: Total number of pages in the PDF
            
        Returns:
            Storage path for the uploaded image
        """
        try:
            # Optimize image for AI analysis using dynamic dimensions
            optimized_image = self._optimize_image_for_analysis(image)
            
            # Convert to PNG format
            image_buffer = io.BytesIO()
            optimized_image.save(image_buffer, format='PNG', optimize=True)
            image_bytes = image_buffer.getvalue()
            
            # Calculate padding for consistent naming (e.g., 001, 002, etc.)
            padding = len(str(total_pages))
            page_str = str(page_num).zfill(padding)
            
            # Create storage path with proper numbering
            storage_path = f"{self.images_prefix}/{task_id}/page_{page_str}.png"
            blob = self.bucket.blob(storage_path)
            
            # Set metadata
            blob.metadata = {
                'task_id': task_id,
                'page_number': str(page_num),
                'total_pages': str(total_pages),
                'upload_time': datetime.now(CET).isoformat(),
                'file_type': 'image',
                'format': 'png',
                'width': str(optimized_image.width),
                'height': str(optimized_image.height),
                'dpi': str(self.target_dpi),
                'cleanup_after': (datetime.now(CET) + timedelta(hours=self.cleanup_after_hours)).isoformat()
            }
            
            # Upload image
            blob.upload_from_string(image_bytes, content_type='image/png')
            
            logger.debug(f"Stored image: {storage_path} ({len(image_bytes)} bytes) - Page {page_num}/{total_pages}")
            return storage_path
            
        except Exception as e:
            logger.error(f"Failed to store image for page {page_num}: {str(e)}")
            return None
    
    def _optimize_image_for_analysis(self, image: Image.Image) -> Image.Image:
        """
        Optimize image for GPT-5 Vision analysis using dynamic dimensions
        
        Args:
            image: Original PIL Image
            
        Returns:
            Optimized PIL Image
        """
        # Ensure RGB mode for consistent processing
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Use dynamic dimensions if available, otherwise keep original size
        if self.max_width and self.max_height:
            # Only resize if image is larger than target dimensions
            if image.width > self.max_width or image.height > self.max_height:
                image.thumbnail((self.max_width, self.max_height), Image.Resampling.LANCZOS)
                logger.debug(f"Resized image to {image.width}x{image.height} (target: {self.max_width}x{self.max_height}, limits: {self.MAX_IMAGE_WIDTH}x{self.MAX_IMAGE_HEIGHT})")
            else:
                logger.debug(f"Image already at optimal size: {image.width}x{image.height} (within {self.MAX_IMAGE_WIDTH}x{self.MAX_IMAGE_HEIGHT} limits)")
        else:
            # Fallback: ensure image doesn't exceed hard limits
            if image.width > self.MAX_IMAGE_WIDTH or image.height > self.MAX_IMAGE_HEIGHT:
                image.thumbnail((self.MAX_IMAGE_WIDTH, self.MAX_IMAGE_HEIGHT), Image.Resampling.LANCZOS)
                logger.debug(f"Applied hard limits: resized to {image.width}x{image.height} (max: {self.MAX_IMAGE_WIDTH}x{self.MAX_IMAGE_HEIGHT})")
            else:
                logger.debug(f"Using original image size: {image.width}x{image.height}")
        
        return image
    
    async def cleanup_task_files(self, task_id: str):
        """
        Clean up all files associated with a task
        
        Args:
            task_id: Unique task identifier
        """
        try:
            if not self.bucket:
                logger.warning("Firebase Storage bucket not initialized - skipping cleanup")
                return
            
            # Clean up PDF files
            pdf_prefix = f"{self.pdf_prefix}/{task_id}/"
            pdf_blobs = list(self.bucket.list_blobs(prefix=pdf_prefix))
            
            # Clean up image files
            images_prefix = f"{self.images_prefix}/{task_id}/"
            image_blobs = list(self.bucket.list_blobs(prefix=images_prefix))
            
            all_blobs = pdf_blobs + image_blobs
            
            if not all_blobs:
                logger.info(f"No files found to clean up for task {task_id}")
                return
            
            # Delete all blobs
            for blob in all_blobs:
                try:
                    blob.delete()
                    logger.debug(f"Deleted: {blob.name}")
                except Exception as e:
                    logger.warning(f"Failed to delete {blob.name}: {str(e)}")
            
            logger.info(f"Cleaned up {len(all_blobs)} files for task {task_id}")
            
        except Exception as e:
            logger.error(f"Error during cleanup for task {task_id}: {str(e)}")
    
    async def cleanup_old_files(self):
        """Clean up files older than the specified cleanup time"""
        try:
            if not self.bucket:
                logger.warning("Firebase Storage bucket not initialized - skipping cleanup")
                return
            
            now = datetime.now(CET)
            deleted_count = 0
            
            # Check both PDF and image prefixes
            for prefix in [self.pdf_prefix, self.images_prefix]:
                blobs = self.bucket.list_blobs(prefix=prefix)
                
                for blob in blobs:
                    try:
                        # Check metadata for cleanup time
                        if blob.metadata and 'cleanup_after' in blob.metadata:
                            cleanup_time = datetime.fromisoformat(blob.metadata['cleanup_after'])
                            if now > cleanup_time:
                                blob.delete()
                                deleted_count += 1
                                logger.debug(f"Deleted expired file: {blob.name}")
                    except Exception as e:
                        logger.warning(f"Error checking/deleting blob {blob.name}: {str(e)}")
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} expired files")
            
        except Exception as e:
            logger.error(f"Error during automatic cleanup: {str(e)}")

    async def get_public_image_url(self, image_path: str) -> str:
        """
        Generate a public Firebase Storage URL with access token for an image
        
        Args:
            image_path: Firebase Storage path for the image
            
        Returns:
            Public URL with access token (format: https://firebasestorage.googleapis.com/v0/b/{bucket}/o/{path}?alt=media&token={token})
        """
        try:
            if not self.bucket:
                raise Exception("Firebase Storage bucket not initialized")
            
            import urllib.parse
            import uuid
            
            logger.info(f"Attempting to generate public URL for: {image_path}")
            
            blob = self.bucket.blob(image_path)
            
            # Check if blob exists
            if not blob.exists():
                logger.error(f"Blob does not exist in Firebase Storage: {image_path}")
                raise Exception(f"Image not found in Firebase Storage: {image_path}")
            
            logger.info(f"Blob exists, reloading metadata for: {image_path}")
            
            # Generate or retrieve access token for the blob
            # Set a download token in metadata if not already present
            blob.reload()
            metadata = blob.metadata or {}
            
            logger.info(f"Current metadata: {metadata}")
            
            if 'firebaseStorageDownloadTokens' not in metadata:
                # Generate a new token
                download_token = str(uuid.uuid4())
                logger.info(f"Generated new token: {download_token}")
                metadata['firebaseStorageDownloadTokens'] = download_token
                blob.metadata = metadata
                blob.patch()
                logger.info(f"Patched blob with new token")
            else:
                download_token = metadata['firebaseStorageDownloadTokens']
                logger.info(f"Using existing token: {download_token}")
            
            # Construct the Firebase Storage public URL with token
            encoded_path = urllib.parse.quote(image_path, safe='')
            public_url = f"https://firebasestorage.googleapis.com/v0/b/{self.bucket_name}/o/{encoded_path}?alt=media&token={download_token}"
            
            logger.info(f"✅ Generated public URL: {public_url}")
            return public_url
            
        except Exception as e:
            logger.error(f"❌ Failed to generate public URL for {image_path}: {str(e)}", exc_info=True)
            raise

# Global storage manager instance
storage_manager = PDFStorageManager()
