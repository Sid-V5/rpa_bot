# src/validator.py
import re
import logging
from datetime import datetime
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class Validator:
    """
    Validates extracted invoice data based on predefined rules.
    """
    def __init__(self, config):
        self.config = config

    def validate_invoice_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validates the extracted invoice data.
        Returns the data with 'status' and 'errors' fields added.
        """
        errors: List[str] = []

        # Validate Invoice Number
        if not data.get("invoice_number"):
            errors.append("Invoice number is missing.")

        # Validate Date
        date_str = data.get("date")
        if not date_str:
            errors.append("Date is missing.")
        else:
            if not self.parse_date(date_str):
                errors.append(f"Date '{date_str}' is not in a recognized format.")

        # Validate Vendor
        vendor_name = data.get("vendor")
        if not vendor_name:
            errors.append("Vendor name is missing.")
        elif len(vendor_name) < 3:
            errors.append(f"Vendor name '{vendor_name}' is too short (min 3 characters).")

        # Validate Total Amount
        total_amount_str = data.get("total_amount")
        if not total_amount_str:
            errors.append("Total amount is missing.")
        else:
            try:
                # Remove currency symbols and commas for conversion
                cleaned_amount = re.sub(r'[$,]', '', total_amount_str)
                total_amount = float(cleaned_amount)
                if total_amount <= 0:
                    errors.append(f"Total amount '{total_amount_str}' must be greater than zero.")
                data["total_amount"] = total_amount # Store as float if valid
            except ValueError:
                errors.append(f"Total amount '{total_amount_str}' is not a valid number.")

        data["status"] = "INVALID" if errors else "VALID"
        data["errors"] = "; ".join(errors) if errors else ""

        if errors:
            logger.warning(f"Validation errors for invoice: {data.get('filename', 'N/A')} - {data['errors']}")
        else:
            logger.info(f"Invoice {data.get('filename', 'N/A')} validated successfully.")

        return data

    def parse_date(self, date_str: str):
        """Try parsing a date string with multiple formats."""
        for fmt in ("%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return None

    def get_validation_summary(self, original_data: Dict[str, Any], validated_data: Dict[str, Any]) -> str:
        """
        Provides a summary of validation results with detailed pattern matching info.
        """
        invoice_num = validated_data.get("invoice_number", "MISSING")
        date = validated_data.get("date", "MISSING")
        vendor = validated_data.get("vendor", "MISSING")
        total = validated_data.get("total_amount", "MISSING")
        status = validated_data.get("status", "UNKNOWN")

        summary_parts = [
            f"Fields validated: INV#{invoice_num}, Date:{date}, Vendor:{vendor}, Total:${total}",
            f"Extraction method: {validated_data.get('extraction_method', 'UNKNOWN')}",
            f"Text length: {validated_data.get('text_length', 0)} chars",
            f"Status: {status}"
        ]

        errors = validated_data.get("errors", "")
        if errors:
            summary_parts.append(f"Issues: {errors}")

        return " | ".join(summary_parts)
