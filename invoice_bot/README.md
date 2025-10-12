# RPA Invoice Processing Bot

A Python-based Robotic Process Automation (RPA) bot for automatically processing PDF invoices. Extracts key data, validates information, and generates reports.

## Features

- **PDF Text Extraction**: Uses pdfplumber for direct text extraction
- **OCR Support**: Falls back to EasyOCR for scanned/image-based PDFs
- **Data Validation**: Validates dates, amounts, and vendor information
- **GUI Interface**: Simple Tkinter GUI for folder selection and processing
- **CSV Reporting**: Generates structured CSV reports of extracted data
- **Email Alerts**: Sends summary emails when validation thresholds are exceeded
- **Configurable**: Uses YAML config file for easy customization
- **Logging**: Comprehensive logging to files and console
- **Docker Ready**: Includes Docker configuration for containerized deployment

## Quick Start

### Requirements
- Python 3.10+
- pip (Python package installer)

### Installation

1. Clone or download the project
2. Navigate to the project directory
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Usage

Run the GUI application:
```bash
python run_bot.py
```

This launches a simple GUI where you can:
- Select an input folder containing PDF invoices
- Click "Start Processing" to process all PDFs
- View progress and results

### Configuration

Edit `config.yaml` to customize:

- Input/output directories
- Email settings (sender, recipient, SMTP credentials)
- OCR settings (languages, retry counts)
- Regex patterns for data extraction
- Validation thresholds

## Sample Data

The `samples/invoices/` folder contains 6 sample PDF files with various formats and validation scenarios:
- invoice_001_valid.pdf: Valid invoice
- invoice_002_invalid_date.pdf: Invalid date format
- invoice_003_missing_total.pdf: Missing total amount
- invoice_004_scanned.pdf: Image-based (needs OCR)
- invoice_005_alt_format.pdf: Different layout
- invoice_006_negative_total.pdf: Invalid negative amount

## Output

Processing generates:
- `output/invoice_report.csv`: Structured CSV with extracted data and validation results
- `logs/bot.log`: Detailed processing logs
- Email alerts (if configured and validation threshold exceeded)

## Docker

Build and run with Docker:
```bash
# Build image
docker build -t rpa-invoice-bot .

# Run with volumes
docker run -v "$(pwd)/samples:/app/samples" -v "$(pwd)/output:/app/output" -v "$(pwd)/logs:/app/logs" rpa-invoice-bot
```

## Configuration

Edit `config.yaml` to customize settings:

- **Paths**: Input/output directories
- **Email**: SMTP settings and thresholds
- **OCR**: Language models and retry settings

## Dependencies

- Python 3.10+
- pdfplumber
- easyocr
- pyyaml
- pandas
- Pillow

Install with: `pip install -r requirements.txt`

## License

MIT License
