# run_bot.py
import sys
import os
import subprocess
import logging

# Set up simple logging for startup checks
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def check_dependencies():
    """Checks for common OCR dependencies to help hobbyist users."""
    try:
        # Check if Tesseract is available (often needed for OCR libraries)
        # Note: EasyOCR is more self-contained, but Tesseract is a common alternative/needed tool
        result = subprocess.run(['tesseract', '--version'], capture_output=True)
        if result.returncode == 0:
            logger.info("External OCR tool (Tesseract) found.")
    except FileNotFoundError:
        logger.warning("Optional: Tesseract not found in PATH. OCR might be slower or use fallback models.")

    # Check for core library imports
    try:
        import pdfplumber
        import easyocr
        import pandas
        logger.info("Core libraries (pdfplumber, easyocr, pandas) verified.")
    except ImportError as e:
        logger.error(f"Missing dependency: {e}. Please run 'pip install -r requirements.txt'")
        sys.exit(1)

def main():
    """Launcher for the Invoice Bot GUI."""
    check_dependencies()
    
    # Add src to path so we can import modules correctly
    sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
    
    try:
        from main import main as start_app
        start_app()
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
