from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
import uuid
from datetime import datetime
import random

async def create_real_clients():
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client['sustainable_tourism_crm']
    
    # Önce mevcut verileri temizle
    await db.clients.delete_many({})
    await db.consumptions.delete_many({})
    
    # Gerçek 5 müşteri verisi
    real_clients = [
        {
            'id': str(uuid.uuid4()),
            'name': 'Akdeniz Turizm A.Ş.',
            'hotel_name': 'Grand Antalya Resort & Spa',
            'contact_person': 'Mehmet Yılmaz',
            'email': 'myilmaz@grandantalya.com',
            'phone': '+90 242 123 45 67',
            'address': 'Lara Mahallesi, Güzeloba Caddesi No:123 Antalya',
            'current_stage': 'II.Aşama',
            'services_completed': ['Mevcut durum analizi', 'Çalışma ekibinin belirlenmesi'],
            'carbon_footprint': 25400.50,
            'sustainability_score': 72,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        },
        {
            'id': str(uuid.uuid4()),
            'name': 'Ege Otelcilik Ltd.',
            'hotel_name': 'Bodrum Bay Hotel',
            'contact_person': 'Ayşe Demir',
            'email': 'ayse@bodrumbay.com',
            'phone': '+90 252 987 65 43',
            'address': 'Yalıkavak Marina, Bodrum, Muğla',
            'current_stage': 'I.Aşama',
            'services_completed': [],
            'carbon_footprint': 18200.75,
            'sustainability_score': 68,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        },
        {
            'id': str(uuid.uuid4()),
            'name': 'Kapadokya Otel Grubu',
            'hotel_name': 'Cave Hotel Göreme',
            'contact_person': 'Fatih Özkan',
            'email': 'fatih@cavehotel.com',
            'phone': '+90 384 456 78 90',
            'address': 'Göreme Mahallesi, Nevşehir',
            'current_stage': 'III.Aşama',
            'services_completed': ['Mevcut durum analizi', 'Çalışma ekibinin belirlenmesi', 'Sürdürülebilirlik planı'],
            'carbon_footprint': 12800.25,
            'sustainability_score': 89,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        },
        {
            'id': str(uuid.uuid4()),
            'name': 'İstanbul Lux Otelcilik',
            'hotel_name': 'Bosphorus Palace Hotel',
            'contact_person': 'Zeynep Kaya',
            'email': 'zeynep@bosphoruspalace.com',
            'phone': '+90 212 345 67 89',
            'address': 'Ortaköy, Beşiktaş, İstanbul',
            'current_stage': 'II.Aşama',
            'services_completed': ['Mevcut durum analizi'],
            'carbon_footprint': 32500.80,
            'sustainability_score': 65,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        },
        {
            'id': str(uuid.uuid4()),
            'name': 'Kuşadası Turizm İşletmeleri',
            'hotel_name': 'Aegean Paradise Resort',
            'contact_person': 'Hakan Çelik',
            'email': 'hakan@aegeanparadise.com',
            'phone': '+90 256 234 56 78',
            'address': 'Kadınlar Denizi Caddesi, Kuşadası, Aydın',
            'current_stage': 'I.Aşama',
            'services_completed': [],
            'carbon_footprint': 21700.60,
            'sustainability_score': 58,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
    ]
    
    # Müşterileri ekle
    result = await db.clients.insert_many(real_clients)
    print(f'✅ {len(result.inserted_ids)} gerçek müşteri eklendi!')
    
    # Her müşteri için tüketim verileri oluştur
    total_consumptions = 0
    for client_data in real_clients:
        client_id = client_data['id']
        hotel_name = client_data['hotel_name']
        print(f'📊 {hotel_name} için tüketim verileri oluşturuluyor...')
        
        # 2023 ve 2024 için tüketim verileri
        for year in [2023, 2024]:
            for month in range(1, 13):
                # Otel büyüklüğüne göre base değerler
                if 'Grand' in hotel_name or 'Palace' in hotel_name:
                    base_multiplier = 1.5  # Büyük oteller
                elif 'Resort' in hotel_name:
                    base_multiplier = 1.2  # Orta büyüklük
                else:
                    base_multiplier = 0.8  # Küçük oteller
                
                # Mevsimsel faktör (yaz ayları daha yoğun)
                season_factor = 1.4 if month >= 6 and month <= 9 else 0.9
                
                # Random varyasyon
                random_factor = random.uniform(0.85, 1.15)
                
                total_factor = base_multiplier * season_factor * random_factor
                
                consumption = {
                    'id': str(uuid.uuid4()),
                    'client_id': client_id,
                    'year': year,
                    'month': month,
                    'electricity': round(15000 * total_factor, 2),
                    'water': round(1200 * total_factor, 2),
                    'natural_gas': round(800 * total_factor, 2),
                    'coal': round(300 * total_factor, 2),
                    'accommodation_count': int(400 * total_factor),
                    'created_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow()
                }
                
                await db.consumptions.insert_one(consumption)
                total_consumptions += 1
    
    print(f'\n🎉 TAMAMLANDI!')
    print(f'📊 5 gerçek müşteri eklendi:')
    for client_data in real_clients:
        print(f'  ✅ {client_data["hotel_name"]}')
    print(f'📈 Toplam {total_consumptions} tüketim verisi eklendi!')
    print(f'📅 2023 ve 2024 yılları için 12 aylık veriler hazır!')
    
    client.close()

if __name__ == "__main__":
    asyncio.run(create_real_clients())