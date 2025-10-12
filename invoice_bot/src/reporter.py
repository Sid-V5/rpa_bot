# src/reporter.py
import pandas as pd
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class Reporter:
    """
    Generates CSV reports and sends email notifications.
    """
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.output_report_path = config['paths']['output_report_path']
        self.email_config = config['email']
        self.sender_email = os.environ.get("SENDER_EMAIL", self.email_config['sender_email'])
        self.sender_password = os.environ.get("SENDER_PASSWORD", self.email_config['sender_password'])

    def generate_report(self, processed_data: List[Dict[str, Any]]):
        """
        Generates a CSV report from the processed invoice data.
        """
        if not processed_data:
            logger.info("No data to report. Skipping CSV generation.")
            return

        try:
            df = pd.DataFrame(processed_data)

            # Enhanced columns with more details
            columns_order = [
                "filename", "extraction_method", "text_length", "confidence_score",
                "invoice_number", "date", "vendor", "total_amount",
                "status", "errors", "validation_details"
            ]

            # Ensure all required columns exist, fill missing with defaults
            for col in columns_order:
                if col not in df.columns:
                    if col == "extraction_method":
                        df[col] = df.get("extraction_method", "UNKNOWN")
                    elif col == "text_length":
                        df[col] = df.get("text_length", 0)
                    elif col == "confidence_score":
                        df[col] = df.get("confidence_score", "N/A")
                    elif col == "validation_details":
                        df[col] = df.get("validation_details", "Basic validation passed")

            df = df.reindex(columns=columns_order)

            output_dir = os.path.dirname(self.output_report_path)
            os.makedirs(output_dir, exist_ok=True)
            df.to_csv(self.output_report_path, index=False)
            logger.info(f"CSV report generated successfully at {self.output_report_path}")

            # Log summary statistics
            total = len(df)
            valid = len(df[df["status"] == "VALID"])
            invalid = len(df[df["status"] == "INVALID"])
            logger.info(f"Report Summary: {valid}/{total} invoices valid, {invalid}/{total} invalid")

        except (IOError, pd.errors.EmptyDataError) as e:
            logger.error(f"Error generating CSV report: {e}", exc_info=True)

    def send_email_notification(self, processed_data: List[Dict[str, Any]]):
        """
        Sends an email notification if the percentage of invalid invoices exceeds the threshold.
        """
        if not self.email_config['enabled']:
            logger.info("Email notifications are disabled in config.yaml.")
            return

        total_invoices = len(processed_data)
        if total_invoices == 0:
            logger.info("No invoices processed, skipping email notification.")
            return

        invalid_invoices = [d for d in processed_data if d.get("status") == "INVALID"]
        num_invalid = len(invalid_invoices)
        invalid_percentage = (num_invalid / total_invoices) * 100

        if invalid_percentage >= self.email_config['threshold_invalid_percentage']:
            logger.info(f"Invalid invoice percentage ({invalid_percentage:.2f}%) "
                        f"exceeds threshold ({self.email_config['threshold_invalid_percentage']}%). Sending email.")
            subject = f"RPA Invoice Bot Alert: {num_invalid}/{total_invoices} Invoices Invalid"
            body = self._create_email_body(processed_data, invalid_invoices, invalid_percentage)
            self._send_email(subject, body)
        else:
            logger.info(f"Invalid invoice percentage ({invalid_percentage:.2f}%) "
                        f"is below threshold ({self.email_config['threshold_invalid_percentage']}%). No email sent.")

    def _create_email_body(self, all_data: List[Dict[str, Any]], invalid_data: List[Dict[str, Any]], invalid_percentage: float) -> str:
        """
        Creates the HTML body for the email notification.
        """
        # This function remains the same, but showing it for completeness
        body = f"""
        <html><body>
            <h2>RPA Invoice Processing Bot Summary</h2>
            <p>Total Invoices Processed: {len(all_data)}</p>
            <p>Invalid Invoices: {len(invalid_data)} ({invalid_percentage:.2f}%)</p>
            <p>Threshold for Alert: {self.email_config['threshold_invalid_percentage']}%</p>
            <h3>Details of Invalid Invoices:</h3>
            <table border="1" style="border-collapse: collapse; padding: 5px;">
                <thead><tr><th>Filename</th><th>Errors</th></tr></thead>
                <tbody>
        """
        for invoice in invalid_data:
            body += f"<tr><td>{invoice.get('filename', 'N/A')}</td><td>{invoice.get('errors', 'N/A')}</td></tr>"
        body += """
                </tbody>
            </table>
            <p>Full report available at: {self.output_report_path}</p>
        </body></html>
        """
        return body

    def _send_email(self, subject: str, body: str):
        """
        Sends an email using SMTP.
        """
        if not self.sender_email or not self.sender_password or not self.email_config['recipient_email']:
            logger.error("Sender email, password, or recipient not configured. Cannot send email.")
            return

        msg = MIMEMultipart()
        msg['From'] = self.sender_email
        msg['To'] = self.email_config['recipient_email']
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))

        try:
            # Using SMTP_SSL for a secure connection
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login(self.sender_email, self.sender_password)
                smtp.send_message(msg)
            logger.info(f"Email notification sent successfully to {self.email_config['recipient_email']}")
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP Authentication Error: {e}. Check sender_email and sender_password (App Password).", exc_info=True)
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}", exc_info=True)
