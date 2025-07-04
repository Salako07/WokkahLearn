# accounts/mailgun_service.py - COMPLETE FIXED VERSION

import requests
import logging
from django.conf import settings
from typing import List, Optional

logger = logging.getLogger(__name__)

class MailgunService:
    """Service for sending emails via Mailgun HTTP API"""
    
    def __init__(self):
        self.api_key = getattr(settings, 'MAILGUN_API_KEY', None)
        self.domain = getattr(settings, 'MAILGUN_DOMAIN', None)
        self.mailgun_url = getattr(settings, 'MAILGUN_URL', 'https://api.mailgun.net')
        self.base_url = f"{self.mailgun_url}/v3/{self.domain}" if self.domain else None
        self.from_email = getattr(settings, 'MAIL_FROM_ADDRESS', 'WokkahLearn <noreply@wokkahlearn.com>')
        self.frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        
        # Use console fallback if Mailgun not configured
        self.use_fallback = not (self.api_key and self.domain)
        
        if self.use_fallback:
            logger.warning("Mailgun not configured. Using console email backend.")
    
    def send_email(
        self, 
        to_emails: List[str], 
        subject: str, 
        text_content: str, 
        html_content: Optional[str] = None,
        from_email: Optional[str] = None
    ) -> bool:
        """
        Send email via Mailgun API or console fallback
        """
        if self.use_fallback:
            return self._send_console_email(to_emails, subject, html_content, text_content)
        else:
            return self._send_mailgun_email(to_emails, subject, text_content, html_content, from_email)
    
    def _send_mailgun_email(
        self, 
        to_emails: List[str], 
        subject: str, 
        text_content: str, 
        html_content: Optional[str] = None,
        from_email: Optional[str] = None
    ) -> bool:
        """Send email via Mailgun API"""
        try:
            # Prepare the data
            data = {
                'from': from_email or self.from_email,
                'to': to_emails,
                'subject': subject,
                'text': text_content,
            }
            
            # Add HTML content if provided
            if html_content:
                data['html'] = html_content
            
            # Make the API request
            response = requests.post(
                f"{self.base_url}/messages",
                auth=("api", self.api_key),
                data=data,
                timeout=30
            )
            
            # Check if successful
            if response.status_code == 200:
                response_data = response.json()
                message_id = response_data.get('id', 'unknown')
                logger.info(f"✅ Email sent successfully via Mailgun. Message ID: {message_id}")
                logger.info(f"   To: {', '.join(to_emails)}")
                logger.info(f"   Subject: {subject}")
                return True
            else:
                logger.error(f"❌ Mailgun API error: {response.status_code}")
                logger.error(f"   Response: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Network error sending email via Mailgun: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error sending email via Mailgun: {e}")
            return False
    
    def _send_console_email(self, to_emails: List[str], subject: str, 
                           html_content: str, text_content: str = None) -> bool:
        """Fallback console email for development."""
        try:
            from django.core.mail import send_mail
            
            # Use text content if available, otherwise strip HTML
            if text_content:
                message = text_content
            else:
                import re
                message = re.sub('<[^<]+?>', '', html_content or '')
            
            send_mail(
                subject=subject,
                message=message,
                from_email=self.from_email,
                recipient_list=to_emails,
                html_message=html_content,
                fail_silently=False
            )
            
            logger.info(f"📧 Console email sent to {', '.join(to_emails)}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Console email failed: {str(e)}")
            return False
    
    def send_verification_email(self, user, verification_token: str) -> bool:
        """Send email verification email"""
        from django.template.loader import render_to_string
        
        try:
            # Build verification URL for frontend
            backend_url = getattr(settings, 'BACKEND_URL', 'http://localhost:8000')
            verification_url = f"{backend_url}/api/auth/verify-email/?token={verification_token}"
            
            # Context for email template
            context = {
                'user': user,
                'verification_url': verification_url,
                'frontend_url': self.frontend_url,
                'company_name': 'WokkahLearn',
                'support_email': 'support@wokkahlearn.com',
                'token': verification_token,  # For debugging
            }
            
            # Render email templates
            html_content = render_to_string('emails/verification/verify_email.html', context)
            text_content = render_to_string('emails/verification/verify_email.txt', context)
            
            # Log the verification URL for debugging
            logger.info(f"🔗 Verification URL: {verification_url}")
            
            # Send email using the main send_email method
            return self.send_email(
                to_emails=[user.email],
                subject='🚀 Verify your WokkahLearn account',
                text_content=text_content,
                html_content=html_content
            )
            
        except Exception as e:
            logger.error(f"❌ Error preparing verification email: {e}")
            return False
    
    def send_welcome_email(self, user) -> bool:
        """Send welcome email after successful verification"""
        from django.template.loader import render_to_string
        
        try:
            context = {
                'user': user,
                'login_url': f"{self.frontend_url}/login",
                'dashboard_url': f"{self.frontend_url}/dashboard",
                'frontend_url': self.frontend_url,
                'company_name': 'WokkahLearn',
            }
            
            # Render email templates
            html_content = render_to_string('emails/verification/welcome.html', context)
            text_content = render_to_string('emails/verification/welcome.txt', context)
            
            # Send email using the main send_email method
            return self.send_email(
                to_emails=[user.email],
                subject='🎉 Welcome to WokkahLearn - Let\'s start coding!',
                text_content=text_content,
                html_content=html_content
            )
            
        except Exception as e:
            logger.error(f"❌ Error preparing welcome email: {e}")
            return False


# Create the service instance
mailgun_service = MailgunService()
