# src/extractor.py
import pdfplumber
from PIL import Image
import easyocr
import logging
import os

logger = logging.getLogger(__name__)

class Extractor:
    """
    Handles text and OCR extraction from PDF files.
    """
    def __init__(self, config):
        self.config = config
        self.ocr_enabled = config['ocr']['enabled']
        self.ocr_lang_list = config['ocr']['model_lang_list']
        self.ocr_retries = config['ocr']['ocr_retries']
        self.model_storage_dir = config['ocr']['model_storage_directory']
        self.gpu_enabled = config['ocr']['gpu']

        # Initialize EasyOCR reader if OCR is enabled
        self.reader = None
        if self.ocr_enabled:
            self._initialize_easyocr()

    def _initialize_easyocr(self):
        """
        Initialize EasyOCR reader with configured parameters
        """
        try:
            self.reader = easyocr.Reader(
                lang_list=self.ocr_lang_list,
                gpu=self.gpu_enabled,
                model_storage_directory=self.model_storage_dir,
                download_enabled=True,
                user_network_directory=None
            )
            logger.info(f"EasyOCR initialized with languages: {self.ocr_lang_list}, GPU: {self.gpu_enabled}")
        except Exception as e:
            logger.error(f"Failed to initialize EasyOCR: {e}")
            self.reader = None
            self.ocr_enabled = False

    def extract_text_from_pdf(self, pdf_path: str) -> dict:
        """
        Extracts text from a PDF file with detailed metadata.
        Prioritizes direct text extraction and falls back to OCR if needed.

        Returns:
            dict: {
                'text': str - extracted text content,
                'extraction_method': str - method used ('OCR' or 'DIRECT'),
                'text_length': int - length of extracted text,
                'confidence_score': str - confidence info for OCR
            }
        """
        logger.info(f"Attempting to extract text from {pdf_path}")

        extraction_result = {
            'text': '',
            'extraction_method': 'UNKNOWN',
            'text_length': 0,
            'confidence_score': 'N/A'
        }

        # Primary method: Direct text extraction using pdfplumber
        direct_text = self._extract_text_with_pdfplumber(pdf_path)
        word_count = len(direct_text.split())

        if word_count >= 50:
            logger.info(f"Successfully extracted {len(direct_text)} characters ({word_count} words) using direct extraction from {os.path.basename(pdf_path)}.")
            extraction_result.update({
                'text': direct_text,
                'extraction_method': 'DIRECT',
                'text_length': len(direct_text),
                'confidence_score': 'HIGH_DIRECT'
            })
            return extraction_result
        else:
            logger.warning(f"Direct extraction yielded only {word_count} words from {pdf_path}. Attempting OCR as fallback.")

        # Fallback method: OCR extraction
        if self.ocr_enabled:
            ocr_text = self._extract_text_with_ocr(pdf_path)
            if ocr_text.strip():
                logger.info(f"Successfully extracted {len(ocr_text)} characters using OCR from {os.path.basename(pdf_path)}.")
                extraction_result.update({
                    'text': ocr_text,
                    'extraction_method': 'OCR',
                    'text_length': len(ocr_text),
                    'confidence_score': 'OCR_COMPLETED'  # EasyOCR doesn't provide overall confidence
                })
                return extraction_result
            else:
                logger.error(f"OCR fallback also failed to extract meaningful text from {pdf_path}. The PDF might be empty or corrupted.")
        else:
            logger.warning(f"No meaningful text extracted directly from {pdf_path} and OCR is disabled.")

        # If both methods fail, return the minimal direct text found
        extraction_result.update({
            'text': direct_text, # Return whatever little was found
            'extraction_method': 'DIRECT_FAILED',
            'text_length': len(direct_text),
        })
        return extraction_result

    def _extract_text_with_pdfplumber(self, pdf_path: str) -> str:
        """
        Extracts text from a PDF using pdfplumber.
        """
        full_text = ""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    full_text += page.extract_text() or ""
            logger.debug(f"Successfully extracted text using pdfplumber from {pdf_path}")
        except pdfplumber.pdf_structures.PDFSyntaxError as e:
            logger.error(f"Invalid PDF structure in {pdf_path}: {e}")
        except Exception as e:
            logger.error(f"Error extracting text with pdfplumber from {pdf_path}: {e}", exc_info=True)
        return full_text

    def _extract_text_with_ocr(self, pdf_path: str) -> str:
        """
        Extracts text from a PDF using OCR (EasyOCR).
        Converts each page to an image and then performs OCR.
        """
        if not self.ocr_enabled or not self.reader:
            return ""

        full_ocr_text = ""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for i, page in enumerate(pdf.pages):
                    logger.debug(f"Performing OCR on page {i+1} of {pdf_path}")
                    # Render page to a Pillow Image object
                    pil_image = page.to_image(resolution=300).original

                    # Convert PIL image to numpy array for EasyOCR
                    import numpy as np
                    img_array = np.array(pil_image)

                    page_text = ""
                    for attempt in range(self.ocr_retries + 1):
                        try:
                            # EasyOCR returns a list of tuples: [(bbox, text, confidence), ...]
                            results = self.reader.readtext(img_array)

                            if results:
                                # Extract text from results and combine with newlines
                                page_text = "\n".join([result[1] for result in results])
                                if page_text.strip():
                                    logger.debug(f"Successfully extracted OCR text on attempt {attempt+1}")
                                    break # Success, break retry loop

                        except Exception as e:
                            logger.warning(f"OCR attempt {attempt+1} failed for page {i+1} of {pdf_path}: {e}")

                        if attempt < self.ocr_retries:
                            logger.debug(f"Retrying OCR for page {i+1} of {pdf_path}...")

                    full_ocr_text += page_text + "\n\n"
            logger.debug(f"Successfully extracted text using EasyOCR from {pdf_path}")
        except Exception as e:
            logger.error(f"Error during EasyOCR extraction from {pdf_path}: {e}", exc_info=True)
            # Don't disable OCR for EasyOCR - it's self-contained and shouldn't have installation issues
        return full_ocr_text
