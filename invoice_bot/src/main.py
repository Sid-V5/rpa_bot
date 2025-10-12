# src/main.py
import tkinter as tk
import yaml
import logging
import logging.config
import os
import sys
from functools import partial
from concurrent.futures import ThreadPoolExecutor, as_completed
from logging.handlers import QueueHandler, QueueListener
import time
from typing import Dict, Any, Callable, List

try:
    # When run as module from src directory (relative imports)
    from .extractor import Extractor
    from .parser import Parser
    from .validator import Validator
    from .reporter import Reporter
    from .gui import InvoiceBotGUI
except ImportError:
    # When run as launcher script (absolute imports)
    from extractor import Extractor
    from parser import Parser
    from validator import Validator
    from reporter import Reporter
    from gui import InvoiceBotGUI

def load_config(config_path: str) -> Dict[str, Any]:
    """Loads configuration from a YAML file."""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except (IOError, yaml.YAMLError) as e:
        logging.error(f"Error loading config file {config_path}: {e}")
        sys.exit(1)

# --- Logging Setup ---
def setup_logging(log_file_path: str) -> tuple[logging.Logger, QueueListener]:
    """Sets up process-safe logging for the application."""
    log_queue = Queue(-1)

    # Create handlers for the listener
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    file_handler = logging.handlers.RotatingFileHandler(
        log_file_path, maxBytes=10485760, backupCount=5
    )
    file_handler.setFormatter(formatter)

    # Create the listener and start it
    listener = QueueListener(log_queue, console_handler, file_handler, respect_handler_level=True)
    listener.start()

    # Configure the root logger of the main process to use the queue
    root = logging.getLogger()
    queue_handler = QueueHandler(log_queue)
    root.addHandler(queue_handler)
    root.setLevel(logging.DEBUG)

    return logging.getLogger(__name__), listener

# --- Core Processing Logic ---
def process_single_invoice(pdf_path: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Processes a single PDF invoice: extracts, parses, and validates data.
    """
    logger = logging.getLogger(__name__)
    filename = os.path.basename(pdf_path)
    logger.info(f"Processing invoice: {filename}")
    
    extractor = Extractor(config)
    parser = Parser(config)
    validator = Validator(config)
    
    extracted_text = ""
    processed_data = {
        "filename": filename,
        "extraction_method": "UNKNOWN",
        "text_length": 0,
        "confidence_score": "N/A"
    }

    try:
        extraction_result = extractor.extract_text_from_pdf(pdf_path)
        extracted_text = extraction_result.get('text', '')
        processed_data.update({
            "extraction_method": extraction_result.get('extraction_method', 'UNKNOWN'),
            "text_length": extraction_result.get('text_length', 0),
            "confidence_score": extraction_result.get('confidence_score', 'N/A')
        })

        if not extracted_text.strip():
            logger.warning(f"No meaningful text extracted from {filename}. Skipping parsing.")
            processed_data.update({
                "invoice_number": None, "date": None, "vendor": None, "total_amount": None,
                "status": "INVALID", "errors": "No text extracted from PDF.",
                "validation_details": "No text to parse"
            })
            return processed_data
    except Exception as e:
        logger.error(f"Failed to extract text from {filename}: {e}", exc_info=True)
        processed_data.update({
            "invoice_number": None, "date": None, "vendor": None, "total_amount": None,
            "status": "INVALID", "errors": f"Extraction error: {e}",
            "validation_details": "Extraction failed"
        })
        return processed_data

    parsed_data = parser.parse_invoice_data(extracted_text)
    parsed_data.update(processed_data)  # Merge extraction details
    validated_data = validator.validate_invoice_data(parsed_data)
    validated_data["validation_details"] = validator.get_validation_summary(parsed_data, validated_data)
    return validated_data

from concurrent.futures import ThreadPoolExecutor, as_completed

def run_bot_logic(invoice_files: List[str], use_ocr: bool, update_progress_callback: Callable[[int, int, str], None], config: Dict[str, Any]):
    """
    Orchestrates the entire invoice processing workflow for a list of files.
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Starting invoice processing for {len(invoice_files)} files. OCR enabled: {use_ocr}")
    update_progress_callback(0, 0, "Starting processing...")

    # Create a copy of the config to modify for this run
    run_config = config.copy()
    run_config['ocr']['enabled'] = use_ocr

    total_pdfs = len(invoice_files)
    if total_pdfs == 0:
        update_progress_callback(0, 0, "No PDF invoices selected. Finished.")
        logger.warning("No PDF invoices selected to process.")
        return

    processed_results = []
    
    # Use threading for performance
    num_threads = min(cpu_count(), 4)
    logger.info(f"Using {num_threads} threads for parallel PDF processing.")

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        future_to_pdf = {executor.submit(process_single_invoice, pdf, run_config): pdf for pdf in invoice_files}
        for i, future in enumerate(as_completed(future_to_pdf)):
            pdf_path = future_to_pdf[future]
            try:
                result = future.result()
                processed_results.append(result)
                update_progress_callback(i + 1, total_pdfs, f"Processed {result.get('filename', 'N/A')}")
                logger.debug(f"Completed processing for {result.get('filename', 'N/A')}")
            except Exception as exc:
                logger.error(f'{pdf_path} generated an exception: {exc}')

    reporter = Reporter(run_config)
    reporter.generate_report(processed_results)
    reporter.send_email_notification(processed_results)

    update_progress_callback(total_pdfs, total_pdfs, "All invoices processed. Report generated.")
    logger.info("Invoice processing completed.")

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "..", "config.yaml")

def main():
    """Main entry point for the RPA Invoice Processing Bot."""
    # Load configuration
    config = load_config(CONFIG_FILE)

    # Setup logging
    log_file_path = os.path.join(os.path.dirname(__file__), "..", config['paths']['log_file_path'])
    logger, listener = setup_logging(log_file_path)

    try:
        logger.info("Application started.")

        # Create a partial function for the callback
        bot_logic_callback = partial(run_bot_logic, config=config)

        # Create and run the GUI
        root = tk.Tk()
        initial_ocr_setting = config.get('ocr', {}).get('enabled', True)
        app = InvoiceBotGUI(root, bot_logic_callback, initial_ocr_setting)
        root.mainloop()
        logger.info("Application closed.")

    except Exception as e:
        logger.error(f"Application failed: {e}", exc_info=True)
    finally:
        listener.stop()

# --- Main Application Entry Point ---
if __name__ == "__main__":
    main()
