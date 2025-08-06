"""
Demo Mode Utilities
Handles demo database operations and sample data management
"""
import os
from datetime import datetime, timedelta
import random
from pymongo import MongoClient

class DemoManager:
    def __init__(self):
        self.is_demo_mode = os.environ.get('DEMO_MODE', 'false').lower() == 'true'
        self.demo_db_name = os.environ.get('DEMO_DB_NAME', 'rotacrm_demo')
        self.prod_db_name = os.environ.get('DB_NAME', 'rotacrm')
        
    def get_database_name(self):
        """Returns appropriate database name based on mode"""
        return self.demo_db_name if self.is_demo_mode else self.prod_db_name
    
    def is_demo(self):
        """Check if currently in demo mode"""
        return self.is_demo_mode
    
    def get_sample_clients(self):
        """Generate sample client data for demo"""
        sample_clients = [
            {
                "id": "demo_client_001",
                "name": "GreenWave Hotel Istanbul",
                "company_name": "GreenWave Hospitality",
                "email": "demo@greenwave.com",
                "phone": "+90 212 555 0101",
                "contact_person": "Ahmet Yılmaz", 
                "address": "Beşiktaş, İstanbul",
                "city": "İstanbul",
                "country": "Türkiye",
                "industry": "Turizm",
                "employee_count": 150,
                "created_at": datetime.now() - timedelta(days=180),
                "status": "active",
                "sustainability_score": 85,
                "certificate_type": "ISO 14001",
                "certificate_expiry": datetime.now() + timedelta(days=90)
            },
            {
                "id": "demo_client_002", 
                "name": "Eco Resort Antalya",
                "company_name": "Sustainable Tourism Ltd",
                "email": "info@ecoresort.com",
                "phone": "+90 242 555 0202",
                "contact_person": "Zeynep Kaya",
                "address": "Kemer, Antalya", 
                "city": "Antalya",
                "country": "Türkiye",
                "industry": "Turizm",
                "employee_count": 250,
                "created_at": datetime.now() - timedelta(days=120),
                "status": "active",
                "sustainability_score": 92,
                "certificate_type": "Green Key",
                "certificate_expiry": datetime.now() + timedelta(days=150)
            },
            {
                "id": "demo_client_003",
                "name": "Smart Business Hotel",
                "company_name": "Tech Hotels Group", 
                "email": "contact@smarthotel.com",
                "phone": "+90 312 555 0303",
                "contact_person": "Can Özkan",
                "address": "Çankaya, Ankara",
                "city": "Ankara", 
                "country": "Türkiye",
                "industry": "Turizm",
                "employee_count": 80,
                "created_at": datetime.now() - timedelta(days=60),
                "status": "active",
                "sustainability_score": 78,
                "certificate_type": "LEED",
                "certificate_expiry": datetime.now() + timedelta(days=200)
            }
        ]
        return sample_clients
    
    def get_sample_consumption_data(self):
        """Generate sample consumption data for demo clients"""
        consumption_data = []
        base_date = datetime.now() - timedelta(days=365)
        
        for client_id in ["demo_client_001", "demo_client_002", "demo_client_003"]:
            for month in range(12):
                month_date = base_date + timedelta(days=month * 30)
                consumption_data.append({
                    "id": f"demo_consumption_{client_id}_{month:02d}",
                    "client_id": client_id,
                    "year": month_date.year,
                    "month": month_date.month,
                    "electricity": random.uniform(15000, 25000),  # kWh
                    "water": random.uniform(800, 1500),           # m³
                    "natural_gas": random.uniform(1200, 2000),   # m³
                    "coal": random.uniform(0, 500),              # kg
                    "accommodation_count": random.randint(800, 1500),
                    "created_at": month_date
                })
        
        return consumption_data
    
    def get_sample_documents(self):
        """Generate sample document metadata for demo"""
        document_types = [
            "Enerji Sertifikası", "Su Analiz Raporu", "Atık Yönetim Belgesi",
            "Çevre İzin Belgesi", "ISO 14001 Sertifikası", "Karbon Ayak İzi Raporu"
        ]
        
        documents = []
        for i, client_id in enumerate(["demo_client_001", "demo_client_002", "demo_client_003"]):
            for j, doc_type in enumerate(document_types):
                documents.append({
                    "id": f"demo_doc_{i}_{j}",
                    "client_id": client_id,
                    "name": f"{doc_type} - 2024",
                    "original_filename": f"{doc_type.replace(' ', '_').lower()}_2024.pdf",
                    "file_size": random.randint(500000, 5000000),
                    "document_type": doc_type,
                    "stage": "Onaylandı",
                    "created_at": datetime.now() - timedelta(days=random.randint(1, 180)),
                    "folder_id": f"folder_{client_id}_{doc_type.replace(' ', '_').lower()}",
                    "upload_date": datetime.now() - timedelta(days=random.randint(1, 180)),
                    "status": "active"
                })
        
        return documents
    
    def get_sample_consultants(self):
        """Generate sample consultant data for demo"""
        consultants = [
            {
                "id": "demo_consultant_001",
                "name": "Sürdürülebilirlik Danışmanı",
                "email": "consultant1@greenwave.com", 
                "phone": "+90 212 555 1001",
                "specialization": "Enerji Verimliliği",
                "experience_years": 8,
                "assigned_clients": ["demo_client_001", "demo_client_002"],
                "created_at": datetime.now() - timedelta(days=200),
                "status": "active"
            },
            {
                "id": "demo_consultant_002",
                "name": "Çevre Uzmanı",
                "email": "consultant2@greenwave.com",
                "phone": "+90 212 555 1002", 
                "specialization": "Atık Yönetimi",
                "experience_years": 5,
                "assigned_clients": ["demo_client_003"],
                "created_at": datetime.now() - timedelta(days=150),
                "status": "active"
            }
        ]
        return consultants

demo_manager = DemoManager()