import os
from fastapi_mail import FastMail, ConnectionConfig, MessageSchema
from pydantic import EmailStr
from jinja2 import Environment, FileSystemLoader
from typing import List, Dict
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
from pathlib import Path
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Get email configuration from environment
gmail_user = os.getenv("GMAIL_USER")
gmail_password = os.getenv("GMAIL_PASSWORD")

logging.info(f"📧 Gmail user: {gmail_user}")
logging.info(f"📧 Gmail password: {'*' * len(gmail_password) if gmail_password else 'None'}")

# Check if email credentials are available
if not gmail_user or not gmail_password:
    logging.warning("⚠️ Gmail credentials not found, email service will be disabled")
    email_service = None
else:
    # Gmail SMTP Configuration
    conf = ConnectionConfig(
        MAIL_USERNAME=gmail_user,
        MAIL_PASSWORD=gmail_password,
        MAIL_FROM=gmail_user,
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
        
        # Log template files for debugging
        try:
            template_files = list(template_dir.glob("*.html"))
            logging.info(f"📧 Found template files: {[f.name for f in template_files]}")
            
            # Check if our specific templates exist
            doc_template = template_dir / "document_upload_tr.html"
            train_template = template_dir / "training_notification_tr.html"
            
            if doc_template.exists():
                logging.info(f"📧 Document template exists: {doc_template}")
                # Read first few lines to verify content
                with open(doc_template, 'r', encoding='utf-8') as f:
                    first_lines = [f.readline().strip() for _ in range(3)]
                logging.info(f"📧 Document template first lines: {first_lines}")
            else:
                logging.error(f"❌ Document template NOT found: {doc_template}")
                
            if train_template.exists():
                logging.info(f"📧 Training template exists: {train_template}")
                # Read first few lines to verify content
                with open(train_template, 'r', encoding='utf-8') as f:
                    first_lines = [f.readline().strip() for _ in range(3)]
                logging.info(f"📧 Training template first lines: {first_lines}")
            else:
                logging.error(f"❌ Training template NOT found: {train_template}")
                
        except Exception as e:
            logging.error(f"❌ Error checking templates: {str(e)}")
    
    async def send_email(self, to_email: str, subject: str, html_content: str, from_email: str = None, from_name: str = None):
        """Send email with HTML content"""
        try:
            # Use custom from_name if provided, otherwise use default
            if not from_name:
                from_name = "ROTA KALİTE & DANIŞMANLIK"
            
            # Use custom from_email if provided, otherwise use configured default
            sender_email = from_email if from_email else gmail_user
            
            message = MessageSchema(
                subject=subject,
                recipients=[to_email],
                body=html_content,
                subtype="html"
            )
            
            # Set the sender with display name
            if from_name:
                message.sender = f"{from_name} <{sender_email}>"
            else:
                message.sender = sender_email
                
            await self.fastmail.send_message(message)
            
            # Log with sender info
            sender_info = f"from {from_name} <{sender_email}>"
            logging.info(f"📧 Email sent to {to_email} {sender_info} with subject: {subject}")
            return True
            
        except Exception as e:
            logging.error(f"❌ Error sending email: {str(e)}")
            raise
    
    async def send_document_upload_notification(
        self, 
        recipient_email: EmailStr, 
        document_name: str,
        upload_date: str,
        folder_path: str = "Klasör belirtilmemiş",
        client_name: str = "Değerli Müşteri",
        sender_name: str = "ROTA CRM",
        sender_role: str = "Sistem"
    ):
        """Send Turkish notification for document upload"""
        try:
            template = self.jinja_env.get_template("document_upload_tr.html")
            html_content = template.render(
                client_name=client_name,
                document_name=document_name,
                upload_date=upload_date,
                folder_path=folder_path,
                sender_name=sender_name,
                sender_role=sender_role
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
        client_name: str = "Değerli Müşteri",
        sender_name: str = "ROTA CRM",
        sender_role: str = "Sistem"
    ):
        """Send Turkish notification for training"""
        try:
            template = self.jinja_env.get_template("training_notification_tr.html")
            html_content = template.render(
                client_name=client_name,
                training_name=training_name,
                training_date=training_date,
                trainer=trainer,
                participant_count=participant_count,
                sender_name=sender_name,
                sender_role=sender_role
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
    
    async def send_bulk_document_notification(
        self, 
        recipient_email: EmailStr, 
        documents: list,
        client_name: str = "Değerli Müşteri"
    ):
        """Send Turkish notification for multiple document uploads"""
        try:
            # Process documents to ensure date formatting
            processed_documents = []
            for doc in documents:
                processed_doc = dict(doc)
                # Format created_at date
                created_at = doc.get('created_at')
                if created_at:
                    if hasattr(created_at, 'strftime'):
                        processed_doc['formatted_date'] = created_at.strftime('%d.%m.%Y %H:%M')
                    else:
                        processed_doc['formatted_date'] = str(created_at)
                else:
                    processed_doc['formatted_date'] = 'Bilinmiyor'
                processed_documents.append(processed_doc)
            
            template = self.jinja_env.get_template("bulk_document_upload_tr.html")
            html_content = template.render(
                client_name=client_name,
                documents=processed_documents,
                total_count=len(documents)
            )
            
            message = MessageSchema(
                subject=f"📄 {len(documents)} Doküman Yükleme Bildirimi",
                recipients=[recipient_email],
                body=html_content,
                subtype="html"
            )
            
            await self.fastmail.send_message(message)
            logging.info(f"📧 Bulk document email sent to {recipient_email} for {len(documents)} documents")
            
        except Exception as e:
            logging.error(f"❌ Error sending bulk document email: {str(e)}")
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
if gmail_user and gmail_password:
    email_service = EmailService()
    logging.info("✅ Email service created successfully")
else:
    email_service = None
    logging.warning("⚠️ Email service disabled due to missing credentials")