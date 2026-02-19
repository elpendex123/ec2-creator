import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, Any
from app.config import settings
import logging

logger = logging.getLogger(__name__)


def send_notification(event: str, instance_data: Dict[str, Any]) -> bool:
    """
    Send email notification for instance lifecycle events.

    Args:
        event: Event type (create, start, stop, destroy)
        instance_data: Instance information

    Returns:
        bool: True if sent successfully, False otherwise
    """
    if not settings.NOTIFICATION_EMAIL or not settings.SMTP_USER:
        logger.warning("Email notifications not configured")
        return False

    try:
        subject = f"EC2 Instance {event.upper()}: {instance_data.get('name', 'unknown')}"

        body = f"""
Instance {event.upper()} Event

Instance ID: {instance_data.get('id', 'N/A')}
Instance Name: {instance_data.get('name', 'N/A')}
State: {instance_data.get('state', 'N/A')}
Public IP: {instance_data.get('public_ip', 'N/A')}
Instance Type: {instance_data.get('instance_type', 'N/A')}
AMI: {instance_data.get('ami', 'N/A')}
Backend Used: {instance_data.get('backend_used', 'N/A')}
Timestamp: {datetime.utcnow().isoformat()}

SSH Command:
{instance_data.get('ssh_string', 'N/A')}
"""

        msg = MIMEMultipart()
        msg["From"] = settings.SMTP_USER
        msg["To"] = settings.NOTIFICATION_EMAIL
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
        server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()

        logger.info(f"Notification sent for event: {event}")
        return True

    except Exception as e:
        logger.error(f"Failed to send notification: {str(e)}")
        return False
