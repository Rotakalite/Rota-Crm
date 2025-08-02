"""
AI Service for Rota-CRM
Provides intelligent suggestions and automatic text generation using OpenAI
Direct OpenAI integration for better stability
"""
import os
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from openai import AsyncOpenAI

class SustainabilityAIService:
    """AI service for sustainability recommendations and text generation"""
    
    def __init__(self):
        self.api_key = os.environ.get('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable not found")
        
        # Initialize OpenAI client
        self.client = AsyncOpenAI(api_key=self.api_key)
        self.model = "gpt-4o-mini"  # Economic choice
        
        logging.info(f"✅ AI Service initialized with {self.model}")
    
    async def _send_message(self, system_message: str, user_message: str) -> str:
        """Send message to OpenAI and get response"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=2048,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logging.error(f"❌ OpenAI API Error: {str(e)}")
            raise Exception(f"OpenAI API hatası: {str(e)}")
    
    async def generate_sustainability_suggestions(self, client_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate intelligent sustainability suggestions based on client data
        """
        try:
            # Extract key metrics
            client_info = client_data.get('client_info', {})
            consumption = client_data.get('consumption_data', {})
            personnel = client_data.get('personnel', [])
            statistics = client_data.get('statistics', {})
            
            hotel_name = client_info.get('hotel_name', client_info.get('name', 'İşletme'))
            total_energy = consumption.get('total_energy', 0) 
            total_water = consumption.get('total_water', 0)
            total_personnel = len(personnel)
            
            # Create prompt in Turkish
            system_message = """Sen sürdürülebilirlik uzmanı bir AI asistanısın. Otel ve turizm sektöründe sürdürülebilirlik konularında profesyonel öneriler veriyorsun. Türkçe olarak net, uygulanabilir ve somut öneriler ver."""
            
            user_prompt = f"""
Otel Bilgileri:
- İşletme Adı: {hotel_name}
- Personel Sayısı: {total_personnel}
- Yıllık Elektrik Tüketimi: {total_energy} kWh
- Yıllık Su Tüketimi: {total_water} m³

Bu verilere göre:

1. ENERJİ VERİMLİLİĞİ ÖNERİLERİ (3 somut öneri):
   - Tasarruf potansiyeli ve maliyet analizi ile

2. SU TASARRUFU ÖNERİLERİ (3 somut öneri):
   - Uygulanabilir çözümler ve beklenen tasarruf oranı ile

3. PERSONEL EĞİTİM ÖNERİLERİ (2 öneri):
   - Sürdürülebilirlik bilinci artırıcı eğitimler

4. ATIK YÖNETİMİ ÖNERİLERİ (2 öneri):
   - Geri dönüşüm ve atık azaltma stratejileri

Her öneri için:
- Net açıklama
- Beklenen fayda/tasarruf
- Uygulama zorluğu (Kolay/Orta/Zor)

Kısa ve öz, uygulanabilir öneriler ver.
            """
            
            # Get AI response
            response = await self._send_message(system_message, user_prompt)
            
            return {
                "suggestions": response,
                "hotel_name": hotel_name,
                "analysis_date": "2024",
                "metrics": {
                    "energy_consumption": total_energy,
                    "water_consumption": total_water,
                    "personnel_count": total_personnel
                }
            }
            
        except Exception as e:
            logging.error(f"❌ AI Suggestions Error: {str(e)}")
            return {
                "error": f"AI öneri oluşturma hatası: {str(e)}",
                "suggestions": "Geçici bir hata oluştu. Lütfen daha sonra tekrar deneyin."
            }
    
    async def generate_report_section_text(self, section_type: str, client_data: Dict[str, Any]) -> str:
        """
        Generate professional text for specific report sections
        """
        try:
            client_info = client_data.get('client_info', {})
            hotel_name = client_info.get('hotel_name', client_info.get('name', 'İşletme'))
            
            system_message = "Sen profesyonel sürdürülebilirlik raporu yazan uzman bir yazarsın. NEST Hotel tarzında profesyonel, resmi ve etkileyici metinler yazıyorsun."
            
            prompts = {
                "sustainability_message": f"""
{hotel_name} için sürdürülebilirlik mesajı yazısı yaz. 
Şu konuları içersin:
- Çevre sorumluluğu
- Gelecek nesiller için çalışma
- Sürdürülebilir turizm anlayışı
- Paydaşlarla işbirliği

Profesyonel, resmi dil kullanın. 2-3 paragraf olsun.
                """,
                
                "environmental_approach": f"""
{hotel_name} için çevre yaklaşımı bölümü yaz.
Şu konuları içersin:
- Doğal kaynakların korunması
- Çevre bilinci
- Kirlilik önleme
- Sürekli iyileştirme

Profesyonel ton, 2-3 paragraf.
                """,
                
                "executive_summary": f"""
{hotel_name} için sürdürülebilirlik raporu yönetici özeti yaz.
Ana başarılar ve 2025 hedefleri içersin.
Kısa ve etkili, 3-4 cümle.
                """
            }
            
            if section_type not in prompts:
                return f"{section_type} bölümü için otomatik metin üretimi hazırlanıyor..."
            
            response = await self._send_message(system_message, prompts[section_type])
            return response
            
        except Exception as e:
            logging.error(f"❌ AI Text Generation Error: {str(e)}")
            return f"Metin üretimi sırasında hata oluştu: {str(e)}"
    
    async def analyze_consumption_trends(self, consumption_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze consumption data and provide trend insights
        """
        try:
            energy_by_month = consumption_data.get('energy_by_month', {})
            water_by_month = consumption_data.get('water_by_month', {})
            
            system_message = "Sen veri analisti bir AI'sın. Tüketim verilerini analiz edip trend analizleri ve öngörüler yapıyorsun."
            
            user_prompt = f"""
Aylık Tüketim Verileri:
Elektrik: {energy_by_month}
Su: {water_by_month}

Bu verileri analiz et ve şunları belirle:

1. TREND ANALİZİ:
   - Yüksek tüketim ayları
   - Düşük tüketim ayları  
   - Mevsimsel etkiler

2. ÖNGÖRÜLER:
   - Gelecek ay tahmini
   - Risk faktörleri
   - Optimizasyon fırsatları

3. EYLEM ÖNERİLERİ:
   - Acil müdahale gereken alanlar
   - Kısa vadeli iyileştirmeler

Kısa ve net analiz yap.
            """
            
            response = await self._send_message(system_message, user_prompt)
            
            return {
                "analysis": response,
                "data_points": len(energy_by_month) + len(water_by_month),
                "analysis_type": "consumption_trends"
            }
            
        except Exception as e:
            logging.error(f"❌ AI Trend Analysis Error: {str(e)}")
            return {
                "error": f"Trend analizi hatası: {str(e)}",
                "analysis": "Veri analizi yapılamadı."
            }
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test OpenAI API connection"""
        try:
            system_message = "Sen yardımcı bir asistansın."
            user_message = "Merhaba! AI servisi test ediliyor. Kısa bir cevap ver."
            
            response = await self._send_message(system_message, user_message)
            
            return {
                "status": "success",
                "message": "AI servisi çalışıyor!",
                "test_response": response,
                "model": self.model
            }
            
        except Exception as e:
            logging.error(f"❌ AI Test Error: {str(e)}")
            return {
                "status": "error", 
                "message": f"AI servisi test hatası: {str(e)}",
                "model": self.model
            }
    
    async def chat_with_context(self, user_question: str, client_data: Dict[str, Any]) -> str:
        """
        AI Chat with client context for informed responses
        """
        try:
            client_info = client_data.get('client_info', {})
            consumption = client_data.get('consumption_data', {})
            personnel = client_data.get('personnel', [])
            
            hotel_name = client_info.get('hotel_name', client_info.get('name', 'İşletme'))
            total_energy = consumption.get('total_energy', 0)
            total_water = consumption.get('total_water', 0)
            
            system_message = f"""Sen {hotel_name} için sürdürülebilirlik uzmanı AI asistanısın. 
            
İşletme Bilgileri:
- İşletme: {hotel_name}
- Personel: {len(personnel)} kişi
- Yıllık Elektrik: {total_energy} kWh
- Yıllık Su: {total_water} m³

Kullanıcının sorularını bu veriler ışığında, profesyonel, pratik ve uygulanabilir şekilde yanıtla. 
Türkçe konuş ve sürdürülebilirlik konularında uzman tavsiyeleri ver."""
            
            response = await self._send_message(system_message, user_question)
            return response
            
        except Exception as e:
            logging.error(f"❌ AI Chat Error: {str(e)}")
            return f"Üzgünüm, sorunuzu cevaplayamadım: {str(e)}"
    
    async def generate_comprehensive_sustainability_report(self, client_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate comprehensive AI-enhanced sustainability report data
        """
        try:
            client_info = client_data.get('client_info', {})
            consumption = client_data.get('consumption_data', {})
            personnel = client_data.get('personnel', [])
            
            hotel_name = client_info.get('hotel_name', client_info.get('name', 'İşletme'))
            
            # Generate multiple sections with AI
            sections = {}
            
            # Executive Summary
            sections['executive_summary'] = await self.generate_report_section_text(
                'executive_summary', client_data
            )
            
            # Environmental Impact Analysis
            system_message = "Sen çevre uzmanısın. Otel için çevresel etki analizi yap."
            env_prompt = f"""
{hotel_name} için detaylı çevresel etki analizi yap:

Mevcut Durum:
- Elektrik: {consumption.get('total_energy', 0)} kWh/yıl
- Su: {consumption.get('total_water', 0)} m³/yıl
- Personel: {len(personnel)} kişi

Analiz et:
1. Mevcut çevresel etki seviyesi
2. Sektör karşılaştırması
3. İyileştirme alanları
4. Risk faktörleri

Profesyonel, sayısal ve detaylı analiz yap.
            """
            
            sections['environmental_analysis'] = await self._send_message(system_message, env_prompt)
            
            # Sustainability Action Plan
            action_system = "Sen sürdürülebilirlik strateji uzmanısın."
            action_prompt = f"""
{hotel_name} için 2025-2026 sürdürülebilirlik eylem planı oluştur:

Şu alanları kapsasın:
1. Kısa vadeli hedefler (3-6 ay)
2. Orta vadeli hedefler (6-12 ay)
3. Uzun vadeli hedefler (1-2 yıl)
4. Bütçe önerileri
5. Başarı metrikleri

Somut, ölçülebilir ve uygulanabilir plan yap.
            """
            
            sections['action_plan'] = await self._send_message(action_system, action_prompt)
            
            # Best Practices Recommendations
            best_practices_system = "Sen otel sürdürülebilirlik uzmanısın."
            best_practices_prompt = f"""
{hotel_name} için sektör best practice önerileri:

1. Enerji verimliliği best practices
2. Su tasarrufu innovative yöntemler
3. Atık azaltma stratejileri
4. Yeşil sertifikasyon yolları
5. Misafir engagement taktikleri

Dünya örnekleri ve başarı hikayeleri ile destekle.
            """
            
            sections['best_practices'] = await self._send_message(best_practices_system, best_practices_prompt)
            
            return {
                **client_data,
                'ai_enhanced_sections': sections,
                'generated_at': datetime.now().isoformat(),
                'ai_model': self.model
            }
            
        except Exception as e:
            logging.error(f"❌ AI Report Generation Error: {str(e)}")
            return {
                **client_data,
                'ai_enhanced_sections': {
                    'error': f"AI rapor üretimi hatası: {str(e)}"
                }
            }

# Global instance
sustainability_ai = SustainabilityAIService()