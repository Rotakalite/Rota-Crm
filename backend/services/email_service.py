import os
from fastapi_mail import FastMail, ConnectionConfig, MessageSchema
from pydantic import EmailStr
from jinja2 import Environment, FileSystemLoader
from typing import List, Dict
import logging
from pathlib import Path

# Gmail SMTP Configuration
conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("GMAIL_USER"),
    MAIL_PASSWORD=os.getenv("GMAIL_PASSWORD"),
    MAIL_FROM=os.getenv("GMAIL_USER"),
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    TEMPLATE_FOLDER=str(Path(__file__).parent.parent / "templates")
)

class EmailService:
    def __init__(self):
        self.fastmail = FastMail(conf)
        template_dir = Path(__file__).parent.parent / "templates"
        self.jinja_env = Environment(loader=FileSystemLoader(str(template_dir)))
        logging.info(f"📧 Email service initialized with template dir: {template_dir}")
    
    async def send_document_upload_notification(
        self, 
        recipient_email: EmailStr, 
        document_name: str,
        upload_date: str,
        client_name: str = "Değerli Müşteri"
    ):
        """Send Turkish notification for document upload"""
        try:
            template = self.jinja_env.get_template("document_upload_tr.html")
            html_content = template.render(
                client_name=client_name,
                document_name=document_name,
                upload_date=upload_date
            )
            
            message = MessageSchema(
                subject="📄 Doküman Yükleme Bildirimi",
                recipients=[recipient_email],
                body=html_content,
                subtype="html"
            )
            
            await self.fastmail.send_message(message)
            logging.info(f"📧 Document upload email sent to {recipient_email}")
            
        except Exception as e:
            logging.error(f"❌ Error sending document upload email: {str(e)}")
            raise
    
    async def send_training_notification(
        self,
        recipient_email: EmailStr,
        training_name: str,
        training_date: str,
        trainer: str,
        participant_count: int,
        client_name: str = "Değerli Müşteri"
    ):
        """Send Turkish notification for training"""
        try:
            template = self.jinja_env.get_template("training_notification_tr.html")
            html_content = template.render(
                client_name=client_name,
                training_name=training_name,
                training_date=training_date,
                trainer=trainer,
                participant_count=participant_count
            )
            
            message = MessageSchema(
                subject="🎓 Eğitim Bildirimi",
                recipients=[recipient_email],
                body=html_content,
                subtype="html"
            )
            
            await self.fastmail.send_message(message)
            logging.info(f"📧 Training email sent to {recipient_email}")
            
        except Exception as e:
            logging.error(f"❌ Error sending training email: {str(e)}")
            raise
    
    async def send_test_email(self, recipient_email: EmailStr):
        """Send test email"""
        try:
            message = MessageSchema(
                subject="🧪 Rota CRM Test Email",
                recipients=[recipient_email],
                body="<h1>Test Email</h1><p>Bu bir test emaildir. Gmail SMTP sistemi çalışıyor! ✅</p>",
                subtype="html"
            )
            
            await self.fastmail.send_message(message)
            logging.info(f"📧 Test email sent to {recipient_email}")
            return True
            
        except Exception as e:
            logging.error(f"❌ Error sending test email: {str(e)}")
            return False

# Global email service instance
email_service = EmailService()