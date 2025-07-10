import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import List, Optional
from webmonitor.models import Space, MonitorResult, MonitorType, MonitorStatus

class EmailService:
    # Service for sending email notifications

    def __init__(self, smtp_host: str = "smtp.gmail.com", smtp_port: int = 587,
                 username: Optional[str] = None, password: Optional[str] = None,
                 from_name: str = "Web Monitor"):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_name = from_name
        self.logger = logging.getLogger(__name__)

    def load_from_config(self) -> bool:
        try:
            from .email_config import get_email_config
            email_config = get_email_config()
            smtp_settings = email_config.get_smtp_settings()

            if smtp_settings:
                self.smtp_host = smtp_settings['smtp_host']
                self.smtp_port = smtp_settings['smtp_port']
                self.username = smtp_settings['username']
                self.password = smtp_settings['password']
                self.from_name = smtp_settings['from_name']
                self.logger.info("Email service configured from config file")
                return True
            else:
                self.logger.warning("No email configuration found")
                return False
        except Exception as e:
            self.logger.error(f"Failed to load email configuration: {e}")
            return False
    
    def send_email(self, recipients: List[str], subject: str, body: str, is_html: bool = False) -> bool:
        if not recipients or not self.username or not self.password:
            self.logger.warning("Email sending failed: missing recipients or credentials")
            return False

        try:
            # Create message
            msg = MIMEMultipart()
            from_address = f"{self.from_name} <{self.username}>" if self.from_name else self.username
            msg['From'] = from_address
            msg['To'] = ", ".join(recipients)
            msg['Subject'] = subject
            
            # Attach body with appropriate content type
            content_type = "html" if is_html else "plain"
            msg.attach(MIMEText(body, content_type))
            
            # Connect to SMTP server and send
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)

            self.logger.info(f"Email sent successfully to {len(recipients)} recipients")
            return True
        except Exception as e:
            self.logger.error(f"Failed to send email: {e}")
            return False

    def test_connection(self) -> tuple[bool, str]:
        if not self.username or not self.password:
            return False, "Missing username or password"

        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
            return True, "Connection successful"
        except Exception as e:
            return False, f"Connection failed: {str(e)}"

    def is_configured(self) -> bool:
        # Check if the email service is properly configured
        return bool(self.username and self.password)

# Global instance
_email_service = None

def get_email_service() -> EmailService:
    # Get the global email service instance
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
        # Try to load configuration from file
        _email_service.load_from_config()
    return _email_service

def reload_email_service() -> bool:
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service.load_from_config()

def send_notification_email(recipients: List[str], subject: str, body: str, is_html: bool = False) -> bool:
    # Helper function to send a notification email
    return get_email_service().send_email(recipients, subject, body, is_html)

def send_monitor_result_email(space: Space, result: MonitorResult, recipients: List[str]) -> bool:
    # Send an email with the monitor result
    subject = f"Update on Space {space.name}: {result.monitor_type.value} is {result.status.value}"
    body = f"""
<h2>Monitor Update for {space.name}</h2>
<p><strong>Monitor ID:</strong> {result.monitor_id}</p>
<p><strong>Status:</strong> {result.status.value}</p>
<p><strong>Type:</strong> {result.monitor_type.value}</p>
<p><strong>Time:</strong> {result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</p>
<p><strong>Response Time:</strong> {result.response_time_ms:.2f} ms</p>
<p><strong>Results:</strong> {result.failed_checks}/{len(result.check_list)} checks failed</p>

<h3>Details:</h3>
<pre>{_format_details(result.details)}</pre>
"""
    return send_notification_email(recipients, subject, body, is_html=True)

def _format_details(details):
    if not details:
        return "No details available"
    
    formatted = []
    for check_type, check_data in details.items():
        formatted.append(f"Check: {check_type}")
        
        if isinstance(check_data, dict):
            for key, value in check_data.items():
                # Format the key with spaces between words
                readable_key = key.replace('_', ' ').capitalize()
                formatted.append(f"  {readable_key}: {value}")
    
    return "\n".join(formatted)

def should_send_notification(result: MonitorResult, previous_result: Optional[MonitorResult]) -> bool:
    # Always notify on first check (when there's no previous result)
    if previous_result is None:
        return result.status == MonitorStatus.UNHEALTHY
        
    # Notify when status changes
    return previous_result.status != result.status
