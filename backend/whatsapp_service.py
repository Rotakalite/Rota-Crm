import httpx
import logging
import os
from typing import Optional
from datetime import datetime

# WhatsApp Service Configuration - Railway Environment
WHATSAPP_SERVICE_URL = os.environ.get('WHATSAPP_SERVICE_URL', 'http://localhost:3001')

# Türkçe mesaj şablonları
DOCUMENT_MESSAGE_TEMPLATE = """🔔 Yeni Dokuman Bildirimi

Merhaba {customer_name},

Sizin için yeni bir dokuman yüklendi:

📄 Dokuman: {document_name}
📂 Klasör: {folder_name}
📅 Yüklenme Tarihi: {upload_date}
📝 Açıklama: {description}

Dokumana erişmek için CRM sisteminize giriş yapabilirsiniz.

İyi günler dileriz! 🌟

---
Rota Kalite & Danışmanlık
www.rotakalitedanismanlik.com"""

TRAINING_MESSAGE_TEMPLATE = """🎓 Yeni Eğitim Bildirimi

Merhaba {customer_name},

Sizin için yeni bir eğitim tanımlandı:

📚 Eğitim: {training_name}
👥 Katılımcı Sayısı: {participant_count} kişi
👨‍🏫 Eğitmen: {trainer}
📅 Tarih: {training_date}
📝 Açıklama: {description}

Eğitim detayları için CRM sisteminize giriş yapabilirsiniz.

Başarılar dileriz! 🚀

---
Rota Kalite & Danışmanlık
www.rotakalitedanismanlik.com"""

class WhatsAppService:
    def __init__(self):
        self.service_url = WHATSAPP_SERVICE_URL
        
    async def get_status(self) -> dict:
        """WhatsApp servis durumunu kontrol et"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.service_url}/status", timeout=5.0)
                if response.status_code == 200:
                    return response.json()
                else:
                    return {"connected": False, "message": "Service unavailable"}
        except Exception as e:
            logging.error(f"WhatsApp servis durumu alınamadı: {e}")
            return {"connected": False, "message": str(e)}
    
    async def get_qr_code(self) -> dict:
        """QR kod al"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.service_url}/qr", timeout=5.0)
                if response.status_code == 200:
                    data = response.json()
                    return {"qr": data.get("qr")}
                else:
                    return {"qr": None, "message": "QR code not available"}
        except Exception as e:
            logging.error(f"QR kod alınamadı: {e}")
            return {"qr": None, "message": str(e)}
    
    async def send_message(self, phone_number: str, message: str) -> dict:
        """WhatsApp mesajı gönder"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.service_url}/send-message",
                    json={
                        "phone": phone_number,
                        "message": message
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    return {"success": True, "message": "Message sent successfully"}
                else:
                    return {"success": False, "message": "Failed to send message"}
                
        except Exception as e:
            logging.error(f"WhatsApp mesaj gönderme hatası: {e}")
            return {"success": False, "message": str(e)}
    
    async def send_test_message(self, phone_number: str) -> dict:
        """Test mesajı gönder"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.service_url}/test",
                    json={"phone_number": phone_number},
                    timeout=10.0
                )
                return response.json()
        except Exception as e:
            logging.error(f"Test mesajı gönderilemedi: {e}")
            return {"success": False, "error": str(e)}
    
    async def send_document_notification(self, customer_name: str, customer_phone: str, 
                                       document_name: str, folder_name: str, description: str = "") -> dict:
        """Dokuman yükleme bildirimi gönder"""
        try:
            message = DOCUMENT_MESSAGE_TEMPLATE.format(
                customer_name=customer_name,
                document_name=document_name,
                folder_name=folder_name,
                upload_date=datetime.now().strftime("%d.%m.%Y %H:%M"),
                description=description or "Açıklama bulunmuyor"
            )
            
            result = await self.send_message(customer_phone, message)
            
            if result.get("success"):
                logging.info(f"Dokuman bildirimi gönderildi: {customer_name} ({customer_phone})")
            else:
                logging.error(f"Dokuman bildirimi gönderilemedi: {result.get('error')}")
            
            return result
            
        except Exception as e:
            logging.error(f"Dokuman bildirimi hatası: {e}")
            return {"success": False, "error": str(e)}
    
    async def send_training_notification(self, customer_name: str, customer_phone: str,
                                       training_name: str, participant_count: int, trainer: str,
                                       training_date: str, description: str = "") -> dict:
        """Eğitim tanımlama bildirimi gönder"""
        try:
            message = TRAINING_MESSAGE_TEMPLATE.format(
                customer_name=customer_name,
                training_name=training_name,
                participant_count=participant_count,
                trainer=trainer,
                training_date=training_date,
                description=description or "Açıklama bulunmuyor"
            )
            
            result = await self.send_message(customer_phone, message)
            
            if result.get("success"):
                logging.info(f"Eğitim bildirimi gönderildi: {customer_name} ({customer_phone})")
            else:
                logging.error(f"Eğitim bildirimi gönderilemedi: {result.get('error')}")
            
            return result
            
        except Exception as e:
            logging.error(f"Eğitim bildirimi hatası: {e}")
            return {"success": False, "error": str(e)}

# Global WhatsApp servis instance'ı
whatsapp_service = WhatsAppService()