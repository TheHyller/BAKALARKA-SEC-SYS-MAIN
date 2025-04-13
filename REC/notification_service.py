import os
import smtplib
import requests
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from datetime import datetime
from config.settings import get_setting

class NotificationService:
    """Service to send email and SMS notifications for security alerts"""
    
    def __init__(self):
        """Initialize the notification service"""
        # Default notification settings
        self.notification_thread = None
        self.last_notification = 0  # Timestamp of last notification sent
    
    def send_email_alert(self, subject, message, image_path=None):
        """Send an email alert
        
        Args:
            subject (str): Subject of the email
            message (str): Message body of the email
            image_path (str, optional): Path to image to attach
        
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        # Get email settings from configuration
        email_settings = get_setting("notifications.email", {})
        
        # Check if email notifications are enabled
        if not email_settings.get("enabled", False):
            print("Email notifications are disabled")
            return False
        
        # Get required settings
        smtp_server = email_settings.get("smtp_server")
        smtp_port = email_settings.get("smtp_port", 587)
        smtp_username = email_settings.get("username")
        smtp_password = email_settings.get("password")
        from_email = email_settings.get("from_email", smtp_username)
        to_email = email_settings.get("to_email")
        
        # Check if all required settings are present
        if not all([smtp_server, smtp_username, smtp_password, to_email]):
            print("Email settings are incomplete. Cannot send email notification.")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add text content
            msg.attach(MIMEText(message, 'plain'))
            
            # Add image attachment if provided
            if image_path and os.path.exists(image_path):
                with open(image_path, 'rb') as img_file:
                    img = MIMEImage(img_file.read())
                    img.add_header('Content-Disposition', 'attachment', filename=os.path.basename(image_path))
                    msg.attach(img)
            
            # Connect to SMTP server and send email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                # Use TLS encryption
                server.starttls()
                # Login to SMTP server
                server.login(smtp_username, smtp_password)
                # Send email
                server.send_message(msg)
                
            print(f"Email notification sent to {to_email}")
            return True
            
        except Exception as e:
            print(f"Failed to send email notification: {e}")
            return False
    
    def send_sms_alert(self, message):
        """Send an SMS alert using a third-party SMS API
        
        Args:
            message (str): Message to send via SMS
        
        Returns:
            bool: True if SMS was sent successfully, False otherwise
        """
        # Get SMS settings from configuration
        sms_settings = get_setting("notifications.sms", {})
        
        # Check if SMS notifications are enabled
        if not sms_settings.get("enabled", False):
            print("SMS notifications are disabled")
            return False
        
        # Get SMS provider settings
        provider = sms_settings.get("provider", "").lower()
        api_key = sms_settings.get("api_key")
        to_number = sms_settings.get("to_number")
        
        # Check if all required settings are present
        if not all([provider, api_key, to_number]):
            print("SMS settings are incomplete. Cannot send SMS notification.")
            return False
        
        try:
            # Implementation for different SMS providers
            if provider == "twilio":
                return self._send_twilio_sms(message, sms_settings)
            elif provider == "vonage" or provider == "nexmo":
                return self._send_vonage_sms(message, sms_settings)
            else:
                print(f"Unsupported SMS provider: {provider}")
                return False
                
        except Exception as e:
            print(f"Failed to send SMS notification: {e}")
            return False
    
    def _send_twilio_sms(self, message, settings):
        """Send SMS using Twilio"""
        try:
            from twilio.rest import Client
            
            account_sid = settings.get("account_sid")
            auth_token = settings.get("api_key")
            from_number = settings.get("from_number")
            to_number = settings.get("to_number")
            
            if not all([account_sid, auth_token, from_number, to_number]):
                print("Incomplete Twilio settings")
                return False
            
            # Initialize Twilio client
            client = Client(account_sid, auth_token)
            
            # Send message
            message = client.messages.create(
                body=message,
                from_=from_number,
                to=to_number
            )
            
            print(f"SMS sent via Twilio: {message.sid}")
            return True
            
        except ImportError:
            print("Twilio library not installed. Please install 'twilio' package.")
            return False
        except Exception as e:
            print(f"Failed to send Twilio SMS: {e}")
            return False
    
    def _send_vonage_sms(self, message, settings):
        """Send SMS using Vonage/Nexmo"""
        try:
            api_key = settings.get("api_key")
            api_secret = settings.get("api_secret")
            from_name = settings.get("from_name", "Security")
            to_number = settings.get("to_number")
            
            if not all([api_key, api_secret, to_number]):
                print("Incomplete Vonage/Nexmo settings")
                return False
            
            # Make API request to Vonage
            url = "https://rest.nexmo.com/sms/json"
            data = {
                "api_key": api_key,
                "api_secret": api_secret,
                "from": from_name,
                "to": to_number,
                "text": message
            }
            
            response = requests.post(url, data=data)
            
            if response.status_code == 200:
                response_data = response.json()
                
                if response_data["messages"][0]["status"] == "0":
                    print(f"SMS sent via Vonage: {response_data['messages'][0]['message-id']}")
                    return True
                else:
                    print(f"Failed to send Vonage SMS: {response_data['messages'][0]['error-text']}")
                    return False
            else:
                print(f"Failed to send Vonage SMS. Status code: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"Failed to send Vonage SMS: {e}")
            return False
    
    def send_notification(self, alert_type, device_name, status, sensor_type=None, image_path=None):
        """Send notifications through configured channels
        
        Args:
            alert_type (str): Type of alert (e.g., 'motion', 'door', 'window')
            device_name (str): Name of the device that triggered the alert
            status (str): Status of the sensor
            sensor_type (str, optional): Type of sensor
            image_path (str, optional): Path to image related to the alert
        """
        # Create a descriptive message
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        alert_message = f"SECURITY ALERT: {alert_type.upper()} detected\n\n"
        alert_message += f"Device: {device_name}\n"
        if sensor_type:
            alert_message += f"Sensor: {sensor_type}\n"
        alert_message += f"Status: {status}\n"
        alert_message += f"Time: {timestamp}\n"
        
        # Create email subject
        subject = f"Security Alert: {alert_type.upper()} detected at {timestamp}"
        
        # Get notification settings
        cooldown_seconds = get_setting("notifications.cooldown_seconds", 60)
        current_time = datetime.now().timestamp()
        
        # Check if cooldown period has elapsed
        if current_time - self.last_notification < cooldown_seconds:
            print(f"Notification cooldown active. Skipping notification.")
            return
        
        # Send notifications in a separate thread to avoid blocking
        def notification_thread():
            # Send email if enabled
            email_enabled = get_setting("notifications.email.enabled", False)
            if email_enabled:
                self.send_email_alert(subject, alert_message, image_path)
            
            # Send SMS if enabled
            sms_enabled = get_setting("notifications.sms.enabled", False)
            if sms_enabled:
                # Create shorter message for SMS
                sms_message = f"ALERT: {alert_type} detected from {device_name} at {timestamp}. Status: {status}"
                self.send_sms_alert(sms_message)
            
            # Update last notification timestamp
            self.last_notification = current_time
        
        # Start the notification thread
        self.notification_thread = threading.Thread(target=notification_thread)
        self.notification_thread.daemon = True
        self.notification_thread.start()

# Create a global instance for easy access
notification_service = NotificationService()