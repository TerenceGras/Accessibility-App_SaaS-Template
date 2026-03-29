"""
LumTrails GPT-5 Vision Scanner Module
====================================

This module handles PDF accessibility analysis using OpenAI's GPT-5 with vision capabilities
for OCR analysis and visual accessibility assessment.

Features:
- Visual content analysis using Firebase Storage
- OCR and text recognition
- Layout and structure assessment
- Color contrast analysis
- Accessibility heuristics from visual inspection
- Parallel page processing with configurable concurrency limit
- Temporary storage management with automatic cleanup
"""

import logging
import os
import asyncio
from typing import Dict, List, Any, Tuple
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

# CET timezone for EU service - all dates stored in CET
CET = ZoneInfo("Europe/Paris")

# Import required modules
from openai import OpenAI
from pdf_scan_prompts import get_pdf_scan_prompt, get_report_text, PDF_SCAN_PROMPT
from pdf_storage import storage_manager

logger = logging.getLogger(__name__)


# GPT-5 Vision API configuration
GPT_MODEL = "gpt-5"
MAX_OUTPUT_TOKENS = 10000
DEFAULT_MAX_CONCURRENT_SCANS = 50


class GPTVisionScanner:
    """GPT-5 Vision-based scanner for PDF accessibility analysis using Firebase Storage"""
    
    def __init__(self):
        """Initialize the GPT Vision scanner"""
        # Strip the API key and remove any BOM characters that may be present
        raw_api_key = os.getenv('OPENAI_API_KEY', '')
        # Remove BOM (\ufeff) and other invisible characters, then strip whitespace
        self.openai_api_key = raw_api_key.replace('\ufeff', '').replace('\ufffe', '').strip()
        self.model = GPT_MODEL
        
        # Get max concurrent scans from environment variable or use default
        self.max_concurrent_scans = int(os.getenv('MAX_CONCURRENT_GPT_SCANS', DEFAULT_MAX_CONCURRENT_SCANS))
        logger.info(f"Max concurrent GPT scans set to: {self.max_concurrent_scans}")
        
        # Initialize OpenAI client with sensible timeout and retries
        if self.openai_api_key:
            self.client = OpenAI(api_key=self.openai_api_key, max_retries=1)
            self.client_available = True
            logger.info("OpenAI client initialized successfully for GPT-5 Vision")
        else:
            self.client = None
            self.client_available = False
            logger.warning("OpenAI client not available - API key not found")
    
    async def analyze_pdf(self, pdf_content: bytes, file_name: str, task_id: str, language: str = "en") -> Dict[str, Any]:
        """
        Analyze PDF using GPT-5 vision capabilities with Firebase Storage
        
        Args:
            pdf_content: The PDF file content as bytes
            file_name: Original filename
            task_id: Unique task identifier
            language: Language code for the analysis prompt (en, fr, de, es, it, pt)
            
        Returns:
            Comprehensive accessibility analysis results
        """
        try:
            # Store language for use in analysis
            self.language = language
            
            # Store PDF in Firebase Storage
            logger.info(f"Storing PDF in Firebase Storage: {file_name}")
            pdf_storage_path = await storage_manager.store_pdf_temporarily(pdf_content, file_name, task_id)
            
            # Convert PDF to images and store in Firebase Storage
            logger.info("Converting PDF to images for analysis")
            image_paths = await storage_manager.convert_pdf_to_images(pdf_storage_path, task_id)
            
            if not image_paths:
                raise Exception("Failed to extract images from PDF")
            
            logger.info(f"Extracted {len(image_paths)} pages for analysis")
            
            # Check if GPT-5 client is available
            if not self.client_available:
                logger.error("OpenAI client not available")
                await storage_manager.cleanup_task_files(task_id)
                return {
                    'status': 'error',
                    'error': 'OpenAI API key not configured',
                    'accessibility_report': 'GPT-5 Vision analysis not available. Configure OpenAI API key.',
                    'tool_info': {
                        'name': 'GPT-5 Vision Scanner',
                        'version': '2.0.0',
                        'model': 'unavailable'
                    }
                }
            
            # Process pages in parallel and compile report
            final_report = await self._process_pages_in_parallel(image_paths, file_name)
            
            # Clean up temporary files
            await storage_manager.cleanup_task_files(task_id)
            
            return {
                'status': 'completed',
                'analysis_type': 'ai_vision_free_text',
                'accessibility_report': final_report,
                'pages_analyzed': len(image_paths),
                'tool_info': {
                    'name': 'GPT-5 Vision Scanner',
                    'version': '2.0.0',
                    'model': self.model,
                    'analysis_type': 'AI Visual Analysis - Parallel Page Processing',
                    'max_concurrent_scans': self.max_concurrent_scans
                },
                'timestamp': datetime.now(CET).isoformat()
            }
            
        except Exception as e:
            logger.error(f"GPT vision analysis error: {str(e)}")
            # Attempt cleanup on error
            try:
                await storage_manager.cleanup_task_files(task_id)
            except:
                pass
            
            return {
                'status': 'error',
                'error': str(e),
                'accessibility_report': f'Analysis failed: {str(e)}',
                'tool_info': {
                    'name': 'GPT-5 Vision Scanner',
                    'version': '2.0.0',
                    'model': self.model
                }
            }
    
    async def _process_pages_in_parallel(self, image_paths: List[str], file_name: str) -> str:
        """
        Process pages in parallel with GPT-5 and compile into final report
        
        Args:
            image_paths: List of Firebase Storage paths for all images
            file_name: Original PDF filename
            
        Returns:
            Compiled accessibility report as a single text blob
        """
        try:
            logger.info(f"Processing {len(image_paths)} pages in parallel with GPT-5 Vision (max {self.max_concurrent_scans} concurrent)")
            
            # Get translated report text for the current language
            lang = getattr(self, 'language', 'en')
            t = get_report_text(lang)
            
            # Start building the compiled report header
            compiled_report = f"""{t['report_title']}
=====================================

{t['document']}: {file_name}
{t['analysis_date']}: {datetime.now(CET).strftime('%Y-%m-%d %H:%M:%S UTC')}
{t['total_pages']}: {len(image_paths)}
{t['analysis_method']}: GPT-5 Vision AI (Parallel Processing - Max {self.max_concurrent_scans} Concurrent)

=====================================

"""
            
            # Step 1: Generate all image URLs first (fast operation)
            logger.info("Step 1: Generating public URLs for all pages...")
            url_generation_tasks = []
            for i, image_path in enumerate(image_paths, 1):
                url_generation_tasks.append(self._generate_image_url(image_path, i))
            
            # Wait for all URLs to be generated
            page_url_results = await asyncio.gather(*url_generation_tasks, return_exceptions=True)
            
            # Step 2: Launch GPT scans in parallel with concurrency limit
            logger.info(f"Step 2: Launching GPT scans with max {self.max_concurrent_scans} concurrent requests...")
            semaphore = asyncio.Semaphore(self.max_concurrent_scans)
            
            async def analyze_with_semaphore(page_data: Tuple[int, str, str]) -> Tuple[int, str, str]:
                """Wrapper to limit concurrent GPT API calls"""
                page_num, image_url, image_path = page_data
                async with semaphore:
                    return await self._analyze_single_page_async(image_url, page_num, image_path)
            
            # Prepare tasks for all pages with valid URLs
            analysis_tasks = []
            for i, result in enumerate(page_url_results, 1):
                if isinstance(result, Exception):
                    logger.error(f"Failed to generate URL for page {i}: {result}")
                    analysis_tasks.append(asyncio.create_task(
                        asyncio.coroutine(lambda: (i, f"Error: Could not generate public URL for page {i}", image_paths[i-1]))()
                    ))
                else:
                    image_url = result
                    analysis_tasks.append(analyze_with_semaphore((i, image_url, image_paths[i-1])))
            
            # Wait for all analyses to complete
            logger.info("Waiting for all GPT scans to complete...")
            page_analysis_results = await asyncio.gather(*analysis_tasks, return_exceptions=True)
            
            # Step 3: Sort results by page number and compile report
            logger.info("Step 3: Compiling final report...")
            sorted_results = sorted(
                [(r if not isinstance(r, Exception) else (0, f"Error: {r}", "unknown")) for r in page_analysis_results],
                key=lambda x: x[0]
            )
            
            for page_num, page_report, image_path in sorted_results:
                page_filename = Path(image_path).name
                page_title = t['page_analysis'].format(page_num=page_num)
                compiled_report += f"""
{page_title}
----------------------------
{t['source']}: {page_filename}

{page_report}

{'='*50}

"""
            
            # Add document summary footer
            summary_intro = t['summary_intro'].format(max_concurrent=self.max_concurrent_scans)
            compiled_report += f"""
{t['analysis_summary']}
================

{summary_intro}

• {t['visual_compliance']}
• {t['color_contrast']}
• {t['text_readability']}
• {t['image_accessibility']}
• {t['navigation_layout']}
• {t['wcag_compliance']}

{t['recommendations_note']}

{t['generated_by']}
"""
            
            return compiled_report.strip()
            
        except Exception as e:
            logger.error(f"Failed to process pages: {str(e)}")
            return f"Analysis failed: {str(e)}"
    
    async def _generate_image_url(self, image_path: str, page_number: int) -> str:
        """
        Generate public URL for an image page
        
        Args:
            image_path: Firebase Storage path for the page image
            page_number: Page number (1-indexed)
            
        Returns:
            Public URL for the image
        """
        try:
            logger.info(f"Generating public URL for page {page_number}")
            image_url = await storage_manager.get_public_image_url(image_path)
            
            if not image_url:
                raise Exception(f"Failed to generate URL for page {page_number}")
            
            logger.info(f"✅ URL generated for page {page_number}")
            return image_url
            
        except Exception as e:
            logger.error(f"Failed to generate URL for page {page_number}: {str(e)}")
            raise
    
    async def _analyze_single_page_async(self, image_url: str, page_number: int, image_path: str) -> Tuple[int, str, str]:
        """
        Analyze a single page with GPT-5 Vision (async wrapper for sync GPT call)
        
        Args:
            image_url: Firebase Storage public URL for the page image
            page_number: Page number (1-indexed)
            image_path: Original image path for reference
            
        Returns:
            Tuple of (page_number, analysis_report, image_path)
        """
        try:
            logger.info(f"🔍 GPT-5 Vision analysis starting for page {page_number}")
            
            # Run the synchronous GPT API call in a thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            page_report = await loop.run_in_executor(
                None,
                self._analyze_single_page_sync,
                image_url,
                page_number
            )
            
            logger.info(f"✅ Page {page_number} analysis completed successfully")
            return (page_number, page_report, image_path)
            
        except Exception as e:
            logger.error(f"❌ Failed to analyze page {page_number}: {str(e)}", exc_info=True)
            return (page_number, f"Error analyzing page {page_number}: {str(e)}", image_path)
    
    def _analyze_single_page_sync(self, image_url: str, page_number: int) -> str:
        """
        Analyze a single page with GPT-5 Vision (synchronous method)
        
        Args:
            image_url: Firebase Storage public URL for the page image
            page_number: Page number (1-indexed)
            
        Returns:
            Free text analysis report for this page
        """
        try:
            logger.info(f" Image URL being sent to GPT-5: {image_url}")
            logger.info(f"🚀 Calling OpenAI GPT-5 API...")
            
            # Get the appropriate language prompt
            prompt = get_pdf_scan_prompt(getattr(self, 'language', 'en'))
            
            response = self.client.responses.create(
                model=GPT_MODEL,  # e.g., "gpt-5"
                reasoning={"effort": "high"},  # choose low/medium/high
                input=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_text",
                                "text": prompt
                            }
                        ]
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_image",
                                "image_url": image_url
                            }
                        ]
                    }
                ],
                max_output_tokens=MAX_OUTPUT_TOKENS,
                timeout=300
            )

            # Extract content from GPT-5 response.output format
            text_parts = []
            
            # GPT-5 uses response.output instead of response.choices
            if hasattr(response, 'output') and response.output: 
                for output_item in response.output:
                    if hasattr(output_item, 'content') and output_item.content:
                        for content_block in output_item.content:
                            if hasattr(content_block, 'type') and content_block.type == "output_text":
                                if hasattr(content_block, 'text'):
                                    text_parts.append(content_block.text)
            
            content = "\n".join(p for p in text_parts if p).strip()
                
            logger.info(f"📝 Total extracted text length: {len(content)}")
            if content:
                logger.info(f"📝 Extracted text preview (first 400 chars): {content[:400]}")
            else:
                logger.warning("⚠️ GPT-5 returned empty or no output_text content")
            
            return content
            
        except Exception as e:
            logger.error(f"❌ Failed to analyze page {page_number}: {str(e)}", exc_info=True)
            return f"Error analyzing page {page_number}: {str(e)}"


# Main function for external use - storage path version
async def run_gpt_vision_scan(storage_path: str, file_name: str = None, task_id: str = None, language: str = "en") -> Dict[str, Any]:
    """
    Run GPT-5 Vision accessibility scan on PDF from Firebase Storage path
    
    Args:
        storage_path: Path to the PDF file in Firebase Storage
        file_name: Original filename (optional)
        task_id: Unique task identifier (optional)
        language: Language code for the analysis prompt (en, fr, de, es, it, pt). Defaults to English.
        
    Returns:
        Comprehensive accessibility analysis results
    """
    # Generate default values if not provided
    if not file_name:
        file_name = Path(storage_path).name
    if not task_id:
        task_id = f"task_{int(datetime.now(CET).timestamp())}"
    
    logger.info(f"Starting GPT-5 Vision scan from Firebase Storage for: {file_name} (language: {language})")
    
    try:
        # Read PDF content from Firebase Storage
        if not storage_manager.bucket:
            raise Exception("Firebase Storage bucket not initialized")
        
        # Download PDF content from storage
        blob = storage_manager.bucket.blob(storage_path)
        pdf_content = blob.download_as_bytes()
        
        # Initialize scanner
        scanner = GPTVisionScanner()
        
        # Analyze the PDF with language support
        results = await scanner.analyze_pdf(pdf_content, file_name, task_id, language)
        
        # Delete the original uploaded PDF from storage (cleanup source file)
        # The analyze_pdf function cleans up its own temp files, but we need to
        # also clean up the original source PDF that was uploaded by the API
        try:
            blob.delete()
            logger.info(f"Deleted original source PDF from storage: {storage_path}")
        except Exception as cleanup_error:
            logger.warning(f"Could not delete source PDF {storage_path}: {cleanup_error}")
        
        logger.info("GPT-5 Vision scan completed successfully")
        return results
        
    except Exception as e:
        logger.error(f"GPT-5 Vision scan failed: {str(e)}", exc_info=True)
        
        # Attempt to clean up source PDF even on error
        try:
            if storage_manager.bucket:
                blob = storage_manager.bucket.blob(storage_path)
                blob.delete()
                logger.info(f"Cleaned up source PDF after error: {storage_path}")
        except Exception as cleanup_error:
            logger.warning(f"Could not clean up source PDF after error: {cleanup_error}")
        
        return {
            'status': 'error',
            'error': str(e),
            'accessibility_report': f'Analysis failed: {str(e)}',
            'tool_info': {
                'name': 'GPT-5 Vision Scanner',
                'version': '2.0.0',
                'model': 'gpt-5'
            }
        }


# Main function for external use - content version
async def run_gpt_vision_scan_with_content(pdf_content: bytes, file_name: str, task_id: str, language: str = "en") -> Dict[str, Any]:
    """
    Run GPT-5 Vision accessibility scan on PDF content using Firebase Storage
    
    Args:
        pdf_content: The PDF file content as bytes
        file_name: Original filename
        task_id: Unique task identifier
        language: Language code for the analysis prompt (en, fr, de, es, it, pt). Defaults to English.
        
    Returns:
        Comprehensive accessibility analysis results
    """
    logger.info(f"Starting GPT-5 Vision scan with content for: {file_name} (language: {language})")
    
    try:
        # Initialize scanner
        scanner = GPTVisionScanner()
        
        # Analyze the PDF with language support
        results = await scanner.analyze_pdf(pdf_content, file_name, task_id, language)
        
        logger.info("GPT-5 Vision scan with content completed successfully")
        return results
        
    except Exception as e:
        logger.error(f"GPT-5 Vision scan with content failed: {str(e)}", exc_info=True)
        return {
            'status': 'error',
            'error': str(e),
            'accessibility_report': f'Analysis failed: {str(e)}',
            'tool_info': {
                'name': 'GPT-5 Vision Scanner',
                'version': '2.0.0',
                'model': 'gpt-5'
            }
        }
