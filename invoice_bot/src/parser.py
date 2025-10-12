# src/parser.py
import re
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class Parser:
    """
    Parses extracted text to find key invoice data using regex patterns.
    """
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.regex_patterns = config['regex_patterns']

    def parse_invoice_data(self, text: str) -> Dict[str, Any]:
        """
        Intelligent parsing of invoice data using both regex patterns and heuristic analysis.
        Falls back to dynamic pattern recognition when specific regex doesn't match.
        """
        parsed_data = {
            "invoice_number": None,
            "date": None,
            "vendor": None,
            "total_amount": None
        }

        # Step 1: Try specific regex patterns first (for known formats)
        parsed_data["invoice_number"] = self._find_pattern(text, self.regex_patterns['invoice_number'], group_index=1)
        parsed_data["date"] = self._find_pattern(text, self.regex_patterns['date'])
        parsed_data["vendor"] = self._find_pattern(text, self.regex_patterns['vendor'], group_index=1)
        parsed_data["total_amount"] = self._find_pattern(text, self.regex_patterns['total_amount'], group_index=1)

        # Step 2: If regex fails, use intelligent extraction
        if not parsed_data["invoice_number"]:
            parsed_data["invoice_number"] = self._intelligent_invoice_extraction(text)

        if not parsed_data["date"]:
            parsed_data["date"] = self._intelligent_date_extraction(text)

        if not parsed_data["vendor"]:
            parsed_data["vendor"] = self._intelligent_vendor_extraction(text)

        if not parsed_data["total_amount"]:
            parsed_data["total_amount"] = self._intelligent_amount_extraction(text)

        logger.debug(f"Parsed data: {parsed_data}")
        return parsed_data

    def _intelligent_invoice_extraction(self, text: str) -> Optional[str]:
        """Extracts invoice/reference numbers using common patterns"""
        # Try various common invoice number patterns
        try:
            patterns = [
                r'\b(?:inv|invoice|bill|order|ref)[^\w]*([A-Za-z0-9\-/]+)',  # INV-001, ORDER123, etc.
                r'\b(\d{4,8})\b',  # Pure 4-8 digit numbers
                r'\b([A-Z]{2,4}[\-\s]?\d{3,6})\b',  # ABC001, INV-2023, etc.
                r'\b(\d+\-\d+|\d+\/\d+)\b',  # Dashed or slashed numbers
            ]

            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match and len(match.group(1).strip()) > 1:  # Ensure meaningful result
                    candidate = match.group(1).strip()
                    # Skip very short or just numeric results that look like amounts
                    if len(candidate) >= 3 and not re.match(r'^\d{1,2}(\.\d{1,2})?$', candidate):
                        return candidate
        except Exception as e:
            logger.warning(f"Intelligent invoice extraction failed: {e}")

        return None

    def _intelligent_date_extraction(self, text: str) -> Optional[str]:
        """Extracts dates using common date formats"""
        try:
            # Try various date formats commonly used in invoices
            date_patterns = [
                r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b',  # DD/MM/YYYY, MM/DD/YYYY
                r'\b(\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{2,4})\b',  # 15 March 2023
            ]

            for pattern in date_patterns:
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if match:
                    return match.group(1).strip()

            # Try to find year patterns and extract nearby date-like content
            year_match = re.search(r'\b(20\d{2}|19\d{2})\b', text)
            if year_match:
                year = year_match.group(1)
                # Look for date context around the year
                year_context = re.search(r'(.{0,20}' + str(year) + r'.{0,20})', text, re.IGNORECASE)
                if year_context:
                    context = year_context.group(1).strip()
                    return context # Return the whole context for now

        except Exception as e:
            logger.warning(f"Intelligent date extraction failed: {e}")

        return None

    def _intelligent_vendor_extraction(self, text: str) -> Optional[str]:
        """Extracts vendor/company names using common patterns and heuristics."""
        try:
            # Heuristic 1: Check the first few lines for a likely company name
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            for line in lines[:5]: # Check the first 5 non-empty lines
                words = line.split()
                # A good candidate is short, capitalized, and not a generic invoice term
                if 1 <= len(words) <= 4 and line.isupper() and not any(keyword in line.lower() for keyword in ['invoice', 'bill', 'receipt', 'inc.', 'ltd.']):
                    logger.debug(f"Found potential vendor '{line}' using top-line heuristic.")
                    return line

            # Heuristic 2: Look for keyword-based patterns
            vendor_patterns = [
                r'\b(?:supplier|company|vendor|from|bill\s*to|sold\s*by|merchant)[:\s]*([A-Z][A-Za-z0-9&.,\'\s]{3,50}?)(?=\n|\r|$|[A-Z]{3,}|total|amount|date)',  # After keywords
                r'\b([A-Z][A-Za-z0-9&.,\'\s]+(?:Ltd|Inc|Corp|LLC|Pvt Ltd|GmbH|Company))\b',  # Company suffixes
                r'\b([A-Z][A-Za-z]{2,20}\s+[A-Z][A-Za-z]{2,20}(?:\s+[A-Z][A-Za-z]{2,20})*)\b',  # Multi-word capitalized names
            ]

            for pattern in vendor_patterns:
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if match and match.group(1).strip():
                    candidate = match.group(1).strip()
                    # Skip very short names or common words
                    if len(candidate) > 3 and not re.search(r'\b(bill|total|amount|date|item|qty|receipt)', candidate, re.IGNORECASE):
                        return candidate

            # Heuristic 3 (Fallback): look for any capitalized multi-word sequence in the first 10 lines
            for line in lines[:10]:
                caps_match = re.findall(r'\b(?:[A-Z][A-Za-z0-9&\.,\']+\s+){1,3}[A-Z][A-Za-z0-9&\.,\']+\b', line)
                if caps_match:
                    for candidate in caps_match:
                        candidate = candidate.strip()
                        if len(candidate) > 4 and len(candidate.split()) <= 4:  # Reasonable company name length
                            return candidate

        except Exception as e:
            logger.warning(f"Intelligent vendor extraction failed: {e}")

        return None

    def _intelligent_amount_extraction(self, text: str) -> Optional[str]:
        """Extracts monetary amounts using common currency patterns"""
        try:
            # Look for common currency patterns, highest amounts first
            amount_patterns = [
                r'\$([\d,]+\.\d{1,2})',  # $1,234.56
                r'\$([0-9]{1,6}(?:,[0-9]{3})*(?:\.[0-9]{1,2})?)',  # $1234.56, $1,234.56
                r'(\d{1,6}(?:,[0-9]{3})*\.\d{2})',  # 1234.56, 1,234.56 (no currency symbol)
                r'€([0-9]{1,6}(?:,[0-9]{3})*(?:\.[0-9]{1,2})?)',  # €1234.56
                r'£([0-9]{1,6}(?:,[0-9]{3})*(?:\.[0-9]{1,2})?)',  # £1234.56
                r'INR\s*([0-9]{1,6}(?:,[0-9]{3})*(?:\.[0-9]{1,2})?)',  # INR 1234.56
            ]

            all_amounts = []
            for pattern in amount_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    amount = re.sub(r'[$,]', '', match.strip())  # Remove currency symbols
                    try:
                        float_val = float(amount) if '.' in amount else float(amount)
                        if float_val > 0:
                            all_amounts.append((float_val, match.strip()))
                    except ValueError:
                        continue

            # Return the highest amount found (likely the total)
            if all_amounts:
                all_amounts.sort(key=lambda x: x[0], reverse=True)
                return all_amounts[0][1]  # Return the formatted amount string

        except Exception as e:
            logger.warning(f"Intelligent amount extraction failed: {e}")

        return None

    def _find_pattern(self, text: str, pattern: str, group_index: int = 0) -> Optional[str]:
        """
        Helper method to find a regex pattern in the text.
        Returns the matched group or None if not found.
        """
        try:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(group_index).strip()
        except IndexError:
            logger.warning(f"Regex pattern '{pattern}' matched, but group index {group_index} is out of range.")
        except Exception as e:
            logger.error(f"Error finding pattern '{pattern}': {e}", exc_info=True)
        return None
