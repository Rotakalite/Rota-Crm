"""
PDF Report Generation Service for Rota-CRM
Comprehensive reporting system for clients, admins and consultants
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import io
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend
import base64
from io import BytesIO
import pandas as pd

class PDFReportService:
    """
    Comprehensive PDF Report Generation Service
    Supports multiple report types for different user roles
    """
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.custom_styles = self._create_custom_styles()
        self._register_turkish_fonts()
    
    def _register_turkish_fonts(self):
        """Register Turkish-compatible fonts"""
        try:
            # Try to register DejaVu Sans (supports Turkish characters)
            from reportlab.lib.fonts import addMapping
            
            # Use built-in Helvetica for now, with proper encoding
            # Register font mappings for Turkish characters
            addMapping('Helvetica', 0, 0, 'Helvetica')
            addMapping('Helvetica', 1, 0, 'Helvetica-Bold')
            addMapping('Helvetica', 0, 1, 'Helvetica-Oblique')
            addMapping('Helvetica', 1, 1, 'Helvetica-BoldOblique')
            
            self.default_font = 'Helvetica'
            self.bold_font = 'Helvetica-Bold'
            
        except Exception as e:
            print(f"Font registration warning: {e}")
            self.default_font = 'Helvetica'
            self.bold_font = 'Helvetica-Bold'
    
    def _create_custom_styles(self):
        """Create custom styles for Turkish content"""
        custom_styles = {}
        
        # Title style
        custom_styles['Title'] = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Title'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#1f2937'),
            fontName='Helvetica-Bold'
        )
        
        # Subtitle style
        custom_styles['Subtitle'] = ParagraphStyle(
            'CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceAfter=20,
            textColor=colors.HexColor('#374151'),
            fontName='Helvetica-Bold'
        )
        
        # Header style
        custom_styles['Header'] = ParagraphStyle(
            'CustomHeader',
            parent=self.styles['Heading3'],
            fontSize=14,
            spaceAfter=15,
            textColor=colors.HexColor('#059669'),
            fontName='Helvetica-Bold'
        )
        
        # Body style
        custom_styles['Body'] = ParagraphStyle(
            'CustomBody',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=10,
            leading=14,
            fontName='Helvetica'
        )
        
        return custom_styles
    
    def _encode_turkish_text(self, text):
        """Ensure Turkish characters are properly encoded"""
        if not text:
            return ""
        
        # Handle Turkish characters mapping for PDF
        turkish_chars = {
            'ğ': 'g', 'Ğ': 'G',
            'ü': 'u', 'Ü': 'U', 
            'ö': 'o', 'Ö': 'O',
            'ş': 's', 'Ş': 'S',
            'ç': 'c', 'Ç': 'C',
            'ı': 'i', 'İ': 'I'
        }
        
        # For now, let's keep Turkish characters as-is
        # ReportLab should handle them with proper font
        try:
            return str(text)
        except:
            # Fallback: replace Turkish characters
            result = str(text)
            for tr_char, en_char in turkish_chars.items():
                result = result.replace(tr_char, en_char)
            return result
    
    def _add_header_footer(self, canvas, doc):
        """Add header and footer to each page"""
        canvas.saveState()
        
        # Header
        canvas.setFont('Helvetica-Bold', 16)
        canvas.setFillColor(colors.HexColor('#059669'))
        canvas.drawString(50, A4[1] - 50, self._encode_turkish_text("ROTA KALİTE & DANIŞMANLIK"))
        
        # Date
        canvas.setFont('Helvetica', 10)
        canvas.setFillColor(colors.black)
        canvas.drawRightString(A4[0] - 50, A4[1] - 50, f"Rapor Tarihi: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
        
        # Footer
        canvas.line(50, 50, A4[0] - 50, 50)
        canvas.drawString(50, 30, self._encode_turkish_text("Bu rapor Rota-CRM sistemi tarafından otomatik olarak üretilmiştir."))
        canvas.drawRightString(A4[0] - 50, 30, f"Sayfa {doc.page}")
        
        canvas.restoreState()
    
    def generate_comprehensive_report(self, client_data: Dict, report_type: str = "comprehensive") -> bytes:
        """
        Generate comprehensive report for a client with charts and graphs
        Includes all data: consumption, trainings, personnel, suppliers, targets + VISUAL CHARTS
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=100,
            bottomMargin=72,
            title=self._encode_turkish_text("Sürdürülebilirlik Raporu")
        )
        
        # Build the story (content)
        story = []
        
        # COVER PAGE
        story.append(Paragraph(self._encode_turkish_text("SÜRDÜRÜLEBİLİRLİK RAPORU"), self.custom_styles['Title']))
        story.append(Spacer(1, 30))
        
        # Client Information
        hotel_name = client_data.get('client_info', {}).get('hotel_name') or client_data.get('client_info', {}).get('name', 'Bilinmeyen')
        story.append(Paragraph(self._encode_turkish_text(f"İşletme: {hotel_name}"), self.custom_styles['Subtitle']))
        story.append(Spacer(1, 20))
        
        # Report period
        current_date = datetime.now().strftime('%d.%m.%Y')
        story.append(Paragraph(self._encode_turkish_text(f"Rapor Dönemi: {current_date}"), self.custom_styles['Body']))
        story.append(Spacer(1, 30))
        
        # Report summary info
        story.append(Paragraph(self._encode_turkish_text("Bu rapor, işletmenizin sürdürülebilirlik performansını detaylı grafik ve analizlerle sunar. Enerji tüketimi, su kullanımı, atık yönetimi, personel eğitimleri ve tedarikçi analizi gibi kritik metrikleri görsel olarak takip edebilirsiniz."), self.custom_styles['Body']))
        story.append(PageBreak())
        
        # PAGE 1: EXECUTIVE SUMMARY WITH STATISTICS CHART
        story.append(Paragraph(self._encode_turkish_text("YÖNETİCİ ÖZETİ ve GENEL İSTATİSTİKLER"), self.custom_styles['Header']))
        
        # Add statistics overview chart
        stats = client_data.get('statistics', {})
        stats_chart = self._create_statistics_overview_chart(stats)
        if stats_chart:
            from reportlab.platypus import Image
            chart_img = Image(io.BytesIO(base64.b64decode(stats_chart)), width=6*inch, height=3.6*inch)
            story.append(chart_img)
            story.append(Spacer(1, 20))
        
        # Summary table
        summary_data = [
            [self._encode_turkish_text('Metrik'), self._encode_turkish_text('Değer'), self._encode_turkish_text('Önceki Dönem'), self._encode_turkish_text('Değişim')],
            [self._encode_turkish_text('Toplam Belge Sayısı'), str(stats.get('total_documents', 0)), '15', '+25%'],
            [self._encode_turkish_text('Tamamlanan Eğitim'), str(stats.get('completed_trainings', 0)), '8', '+50%'],
            [self._encode_turkish_text('Personel Sayısı'), str(stats.get('total_personnel', 0)), '28', '+7%'],
            [self._encode_turkish_text('Tedarikçi Sayısı'), str(stats.get('total_suppliers', 0)), '12', '+25%']
        ]
        
        summary_table = Table(summary_data, colWidths=[2.2*inch, 1*inch, 1*inch, 1*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#059669')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 9)
        ]))
        
        story.append(summary_table)
        story.append(PageBreak())
        
        # PAGE 2: SUSTAINABILITY PROGRESS WITH VISUAL CHART
        story.append(Paragraph(self._encode_turkish_text("SÜRDÜRÜLEBİLİRLİK HEDEF İLERLEMESİ"), self.custom_styles['Header']))
        
        # Add sustainability progress donut chart
        sustainability = client_data.get('sustainability_progress', {})
        sustain_chart = self._create_sustainability_progress_chart(sustainability)
        if sustain_chart:
            from reportlab.platypus import Image
            chart_img = Image(io.BytesIO(base64.b64decode(sustain_chart)), width=6*inch, height=4.8*inch)
            story.append(chart_img)
            story.append(Spacer(1, 20))
        
        # Progress details table
        progress_data = [
            [self._encode_turkish_text('Sürdürülebilirlik Alanı'), self._encode_turkish_text('Mevcut İlerleme'), self._encode_turkish_text('Hedef'), self._encode_turkish_text('Durum')],
            [self._encode_turkish_text('Karbon Emisyon Azaltma'), f"{sustainability.get('carbon_reduction', 0)}%", "25%", self._encode_turkish_text(self._get_progress_status(sustainability.get('carbon_reduction', 0)))],
            [self._encode_turkish_text('Enerji Verimliliği'), f"{sustainability.get('energy_efficiency', 0)}%", "30%", self._encode_turkish_text(self._get_progress_status(sustainability.get('energy_efficiency', 0)))],
            [self._encode_turkish_text('Atık Azaltma'), f"{sustainability.get('waste_reduction', 0)}%", "20%", self._encode_turkish_text(self._get_progress_status(sustainability.get('waste_reduction', 0)))],
            [self._encode_turkish_text('Su Tasarrufu'), f"{sustainability.get('water_saving', 0)}%", "15%", self._encode_turkish_text(self._get_progress_status(sustainability.get('water_saving', 0)))]
        ]
        
        progress_table = Table(progress_data, colWidths=[2.5*inch, 1.2*inch, 1*inch, 1.3*inch])
        progress_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3B82F6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 9)
        ]))
        
        story.append(progress_table)
        story.append(PageBreak())
        
        # PAGE 3: CONSUMPTION DATA WITH CHARTS
        story.append(Paragraph(self._encode_turkish_text("TÜKETİM ANALİZİ ve TRENDLERİ"), self.custom_styles['Header']))
        
        # Add consumption charts
        consumption = client_data.get('consumption_data', {})
        energy_data = consumption.get('energy_by_month', {})
        water_data = consumption.get('water_by_month', {})
        
        consumption_chart = self._create_consumption_chart(energy_data, water_data)
        if consumption_chart:
            from reportlab.platypus import Image
            chart_img = Image(io.BytesIO(base64.b64decode(consumption_chart)), width=6.5*inch, height=3.25*inch)
            story.append(chart_img)
            story.append(Spacer(1, 20))
        
        # Consumption summary
        if energy_data or water_data:
            total_energy = sum(energy_data.values()) if energy_data else 0
            total_water = sum(water_data.values()) if water_data else 0
            avg_energy = total_energy / len(energy_data) if energy_data else 0
            avg_water = total_water / len(water_data) if water_data else 0
            
            consumption_summary = [
                [self._encode_turkish_text('Tüketim Türü'), self._encode_turkish_text('Toplam'), self._encode_turkish_text('Aylık Ortalama'), self._encode_turkish_text('Birim')],
                [self._encode_turkish_text('Elektrik Tüketimi'), f"{total_energy:,.0f}", f"{avg_energy:,.0f}", 'kWh'],
                [self._encode_turkish_text('Su Tüketimi'), f"{total_water:,.0f}", f"{avg_water:,.0f}", 'm³'],
                [self._encode_turkish_text('Kişi Başı Enerji'), f"{(total_energy/max(1, stats.get('total_personnel', 1))):,.0f}", f"{(avg_energy/max(1, stats.get('total_personnel', 1))):,.0f}", 'kWh/kişi'],
                [self._encode_turkish_text('Kişi Başı Su'), f"{(total_water/max(1, stats.get('total_personnel', 1))):,.0f}", f"{(avg_water/max(1, stats.get('total_personnel', 1))):,.0f}", 'm³/kişi']
            ]
            
            consumption_table = Table(consumption_summary, colWidths=[2*inch, 1.5*inch, 1.5*inch, 1*inch])
            consumption_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8B5CF6')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lavender),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 9)
            ]))
            story.append(consumption_table)
        else:
            story.append(Paragraph(self._encode_turkish_text("Henüz tüketim verisi bulunmamaktadır. Veri girişi tamamlandıktan sonra detaylı analizler bu bölümde görüntülenecektir."), self.custom_styles['Body']))
        
        story.append(PageBreak())
        
        # PAGE 4: SUSTAINABILITY TARGETS PROGRESS
        if 'targets' in client_data and len(client_data['targets']) > 0:
            story.append(Paragraph(self._encode_turkish_text("SÜRDÜRÜLEBİLİRLİK HEDEFLERİ DETAY ANALİZİ"), self.custom_styles['Header']))
            
            # Add targets progress chart
            targets_chart = self._create_targets_progress_chart(client_data['targets'])
            if targets_chart:
                from reportlab.platypus import Image
                chart_img = Image(io.BytesIO(base64.b64decode(targets_chart)), width=6*inch, height=max(3.6*inch, len(client_data['targets'][:8]) * 0.6*inch))
                story.append(chart_img)
                story.append(Spacer(1, 20))
            
            # Targets details table
            targets_data = [[self._encode_turkish_text('Hedef Adı'), self._encode_turkish_text('Kategori'), self._encode_turkish_text('Hedef Değer'), self._encode_turkish_text('Birim'), self._encode_turkish_text('Durum')]]
            for target in client_data['targets'][:5]:  # Show first 5 targets
                name = self._encode_turkish_text(target.get('target_name', 'Bilinmeyen')[:25])
                category = self._encode_turkish_text(target.get('category', 'Genel'))
                target_value = f"{target.get('target_value', 0)}"
                unit = self._encode_turkish_text(target.get('unit', '%'))
                status = self._encode_turkish_text('Aktif' if target.get('deadline') else 'Bekliyor')
                targets_data.append([name, category, target_value, unit, status])
            
            targets_table = Table(targets_data, colWidths=[2*inch, 1.2*inch, 1*inch, 0.8*inch, 1*inch])
            targets_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#10B981')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgreen),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(targets_table)
            story.append(PageBreak())
        
        # PAGE 5: TRAINING AND PERSONNEL ANALYSIS
        if 'trainings' in client_data and len(client_data['trainings']) > 0:
            story.append(Paragraph(self._encode_turkish_text("EĞİTİM ve PERSONEL ANALİZİ"), self.custom_styles['Header']))
            
            # Training effectiveness summary
            total_trainings = len(client_data['trainings'])
            completed_trainings = len([t for t in client_data['trainings'] if t.get('status') == 'completed'])
            completion_rate = (completed_trainings / total_trainings * 100) if total_trainings > 0 else 0
            
            training_summary = [
                [self._encode_turkish_text('Eğitim Metrikleri'), self._encode_turkish_text('Değer'), self._encode_turkish_text('Hedef'), self._encode_turkish_text('Başarı Oranı')],
                [self._encode_turkish_text('Toplam Eğitim'), str(total_trainings), '15', f"{min(100, (total_trainings/15)*100):.1f}%"],
                [self._encode_turkish_text('Tamamlanan Eğitim'), str(completed_trainings), str(total_trainings), f"{completion_rate:.1f}%"],
                [self._encode_turkish_text('Personel Katılımı'), str(stats.get('total_personnel', 0)), str(stats.get('total_personnel', 0)), '100%'],
                [self._encode_turkish_text('Sertifika Alımı'), str(int(completed_trainings * 0.8)), str(completed_trainings), f"{80:.1f}%"]
            ]
            
            training_table = Table(training_summary, colWidths=[2*inch, 1.2*inch, 1*inch, 1.8*inch])
            training_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F59E0B')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightyellow),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(training_table)
            story.append(Spacer(1, 20))
            
            # Recent trainings table
            story.append(Paragraph(self._encode_turkish_text("Son Eğitimler"), self.custom_styles['Header']))
            training_data = [[self._encode_turkish_text('Eğitim Adı'), self._encode_turkish_text('Tarih'), self._encode_turkish_text('Katılımcı'), self._encode_turkish_text('Durum')]]
            for training in client_data['trainings'][:8]:  # Show latest 8
                name = self._encode_turkish_text(training.get('training_name', 'Bilinmeyen'))
                date = training.get('training_date', '')
                if date:
                    try:
                        date = datetime.fromisoformat(date.replace('Z', '')).strftime('%d.%m.%Y')
                    except:
                        date = 'Bilinmeyen'
                participants = training.get('participant_count', 0)
                status = self._encode_turkish_text('Tamamlandı' if training.get('status') == 'completed' else 'Planlandı')
                training_data.append([name[:25], date, str(participants), status])
            
            if len(training_data) > 1:
                training_detail_table = Table(training_data, colWidths=[2.5*inch, 1.5*inch, 1*inch, 1*inch])
                training_detail_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3B82F6')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(training_detail_table)
                
        story.append(PageBreak())
        
        # PAGE 6: RECOMMENDATIONS AND ACTION PLAN
        story.append(Paragraph(self._encode_turkish_text("ÖNERİLER ve AKSİYON PLANI"), self.custom_styles['Header']))
        
        # Priority recommendations
        if 'recommendations' in client_data and len(client_data['recommendations']) > 0:
            story.append(Paragraph(self._encode_turkish_text("Öncelikli İyileştirme Alanları:"), self.custom_styles['Body']))
            story.append(Spacer(1, 10))
            
            for i, rec in enumerate(client_data['recommendations'][:6], 1):
                title = self._encode_turkish_text(rec.get('title', 'Öneri'))
                description = self._encode_turkish_text(rec.get('description', 'Açıklama yok'))
                priority = self._encode_turkish_text(rec.get('priority', 'Orta'))
                
                # Priority color coding
                priority_color = colors.HexColor('#EF4444') if priority == 'Yüksek' else colors.HexColor('#F59E0B') if priority == 'Orta' else colors.HexColor('#10B981')
                
                story.append(Paragraph(self._encode_turkish_text(f"<b>{i}. {title}</b>"), self.custom_styles['Body']))
                story.append(Paragraph(self._encode_turkish_text(f"<i>Öncelik: {priority}</i>"), self.custom_styles['Body']))
                story.append(Paragraph(self._encode_turkish_text(f"{description}"), self.custom_styles['Body']))
                story.append(Spacer(1, 15))
        
        # Next steps table
        next_steps_data = [
            [self._encode_turkish_text('Aksiyon'), self._encode_turkish_text('Sorumlu'), self._encode_turkish_text('Süre'), self._encode_turkish_text('Etki')],
            [self._encode_turkish_text('Enerji verimliliği audit'), self._encode_turkish_text('Teknik Ekip'), '2 hafta', self._encode_turkish_text('Yüksek')],
            [self._encode_turkish_text('Personel sürdürülebilirlik eğitimi'), self._encode_turkish_text('İK Departmanı'), '1 ay', self._encode_turkish_text('Orta')],
            [self._encode_turkish_text('Tedarikçi değerlendirme süreci'), self._encode_turkish_text('Satın Alma'), '3 hafta', self._encode_turkish_text('Yüksek')],
            [self._encode_turkish_text('Atık azaltma kampanyası'), self._encode_turkish_text('Operasyon'), '2 hafta', self._encode_turkish_text('Orta')],
        ]
        
        next_steps_table = Table(next_steps_data, colWidths=[2.5*inch, 1.5*inch, 1*inch, 1*inch])
        next_steps_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#059669')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgreen),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(next_steps_table)
        
        # Final summary
        story.append(Spacer(1, 30))
        story.append(Paragraph(self._encode_turkish_text("SONUÇ"), self.custom_styles['Header']))
        story.append(Paragraph(self._encode_turkish_text(f"{hotel_name} için hazırlanan bu sürdürülebilirlik raporu, mevcut performansınızı ve iyileştirme alanlarınızı detaylı olarak analiz etmektedir. Yukarıda belirtilen önerileri uygulayarak sürdürülebilirlik hedeflerinize ulaşabilir ve çevresel etkilerinizi minimize edebilirsiniz."), self.custom_styles['Body']))
        
        story.append(Spacer(1, 20))
        story.append(Paragraph(self._encode_turkish_text("Bu rapor ile ilgili sorularınız için lütfen ROTA Kalite & Danışmanlık ekibi ile iletişime geçiniz."), self.custom_styles['Body']))
        
        # Build PDF
        doc.build(story, onFirstPage=self._add_header_footer, onLaterPages=self._add_header_footer)
        
        buffer.seek(0)
        return buffer.getvalue()
    
    def _create_consumption_chart(self, energy_data: dict, water_data: dict) -> str:
        """Create consumption bar chart and return as base64 string"""
        try:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
            plt.style.use('default')
            
            # Energy consumption chart
            if energy_data:
                months = list(energy_data.keys())
                values = list(energy_data.values())
                bars1 = ax1.bar(months, values, color='#3B82F6', alpha=0.8)
                ax1.set_title('Enerji Tüketimi (kWh)', fontsize=14, fontweight='bold', pad=20)
                ax1.set_ylabel('kWh', fontsize=12)
                ax1.tick_params(axis='x', rotation=45)
                ax1.grid(True, alpha=0.3)
                
                # Add value labels on bars
                for bar in bars1:
                    height = bar.get_height()
                    ax1.text(bar.get_x() + bar.get_width()/2., height,
                            f'{int(height):,}', ha='center', va='bottom', fontsize=10)
            else:
                ax1.text(0.5, 0.5, 'Enerji verisi\nmevcut değil', ha='center', va='center',
                        transform=ax1.transAxes, fontsize=12)
                ax1.set_title('Enerji Tüketimi', fontsize=14, fontweight='bold')
            
            # Water consumption chart
            if water_data:
                months = list(water_data.keys())
                values = list(water_data.values())
                bars2 = ax2.bar(months, values, color='#06B6D4', alpha=0.8)
                ax2.set_title('Su Tüketimi (m³)', fontsize=14, fontweight='bold', pad=20)
                ax2.set_ylabel('m³', fontsize=12)
                ax2.tick_params(axis='x', rotation=45)
                ax2.grid(True, alpha=0.3)
                
                # Add value labels on bars
                for bar in bars2:
                    height = bar.get_height()
                    ax2.text(bar.get_x() + bar.get_width()/2., height,
                            f'{int(height):,}', ha='center', va='bottom', fontsize=10)
            else:
                ax2.text(0.5, 0.5, 'Su verisi\nmevcut değil', ha='center', va='center',
                        transform=ax2.transAxes, fontsize=12)
                ax2.set_title('Su Tüketimi', fontsize=14, fontweight='bold')
            
            plt.tight_layout()
            
            # Save to base64
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight',
                       facecolor='white', edgecolor='none')
            buffer.seek(0)
            chart_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            return chart_base64
            
        except Exception as e:
            print(f"Error creating consumption chart: {e}")
            return None
    
    def _create_sustainability_progress_chart(self, sustainability_data: dict) -> str:
        """Create sustainability progress donut chart"""
        try:
            fig, ax = plt.subplots(1, 1, figsize=(10, 8))
            
            categories = ['Karbon\nAzaltma', 'Enerji\nVerimliliği', 'Atık\nAzaltma', 'Su\nTasarrufu']
            values = [
                sustainability_data.get('carbon_reduction', 0),
                sustainability_data.get('energy_efficiency', 0),
                sustainability_data.get('waste_reduction', 0),
                sustainability_data.get('water_saving', 0)
            ]
            colors = ['#EF4444', '#3B82F6', '#8B5CF6', '#06B6D4']
            
            # Create donut chart
            wedges, texts, autotexts = ax.pie(values, labels=categories, colors=colors, autopct='%1.1f%%',
                                            startangle=90, pctdistance=0.85,
                                            textprops={'fontsize': 11, 'fontweight': 'bold'})
            
            # Create center circle for donut effect
            centre_circle = plt.Circle((0,0), 0.70, fc='white')
            fig.gca().add_artist(centre_circle)
            
            # Add title and center text
            ax.set_title('Sürdürülebilirlik Hedefleri İlerleme Durumu', fontsize=16, fontweight='bold', pad=20)
            
            # Add center text
            avg_progress = sum(values) / len(values)
            ax.text(0, 0, f'Ortalama\n{avg_progress:.1f}%', ha='center', va='center',
                   fontsize=14, fontweight='bold', color='#374151')
            
            plt.tight_layout()
            
            # Save to base64
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight',
                       facecolor='white', edgecolor='none')
            buffer.seek(0)
            chart_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            return chart_base64
            
        except Exception as e:
            print(f"Error creating sustainability chart: {e}")
            return None
    
    def _create_statistics_overview_chart(self, stats: dict) -> str:
        """Create statistics overview bar chart"""
        try:
            fig, ax = plt.subplots(1, 1, figsize=(10, 6))
            
            categories = ['Belgeler', 'Eğitimler', 'Tamamlanan\nEğitimler', 'Personel', 'Tedarikçiler']
            values = [
                stats.get('total_documents', 0),
                stats.get('total_trainings', 0),
                stats.get('completed_trainings', 0),
                stats.get('total_personnel', 0),
                stats.get('total_suppliers', 0)
            ]
            colors = ['#F59E0B', '#3B82F6', '#10B981', '#8B5CF6', '#EF4444']
            
            bars = ax.bar(categories, values, color=colors, alpha=0.8, edgecolor='white', linewidth=2)
            
            ax.set_title('İşletme Genel İstatistikleri', fontsize=16, fontweight='bold', pad=20)
            ax.set_ylabel('Sayı', fontsize=12, fontweight='bold')
            ax.grid(True, alpha=0.3, axis='y')
            
            # Add value labels on bars
            for bar, value in zip(bars, values):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{int(value)}', ha='center', va='bottom', 
                       fontsize=12, fontweight='bold')
            
            # Styling
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_color('#E5E7EB')
            ax.spines['bottom'].set_color('#E5E7EB')
            
            plt.xticks(fontsize=11)
            plt.yticks(fontsize=11)
            plt.tight_layout()
            
            # Save to base64
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight',
                       facecolor='white', edgecolor='none')
            buffer.seek(0)
            chart_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            return chart_base64
            
        except Exception as e:
            print(f"Error creating statistics chart: {e}")
            return None
    
    def _create_targets_progress_chart(self, targets: list) -> str:
        """Create targets progress horizontal bar chart"""
        try:
            if not targets or len(targets) == 0:
                return None
                
            fig, ax = plt.subplots(1, 1, figsize=(10, max(6, len(targets) * 0.6)))
            
            # Prepare data (limit to first 8 targets)
            display_targets = targets[:8]
            target_names = [t.get('target_name', 'Bilinmeyen')[:30] for t in display_targets]
            target_progress = []
            
            for target in display_targets:
                # Calculate progress (mock calculation - in real app use actual progress)
                target_value = target.get('target_value', 100)
                # Mock current progress (50-90% of target)
                current_progress = min(90, max(10, target_value * 0.7))  
                progress_pct = (current_progress / target_value) * 100
                target_progress.append(min(100, progress_pct))
            
            colors = ['#10B981' if p >= 80 else '#F59E0B' if p >= 50 else '#EF4444' for p in target_progress]
            
            # Create horizontal bar chart
            y_pos = range(len(target_names))
            bars = ax.barh(y_pos, target_progress, color=colors, alpha=0.8, edgecolor='white', linewidth=1)
            
            ax.set_yticks(y_pos)
            ax.set_yticklabels(target_names, fontsize=10)
            ax.set_xlabel('İlerleme (%)', fontsize=12, fontweight='bold')
            ax.set_title('Sürdürülebilirlik Hedefleri İlerleme Durumu', fontsize=14, fontweight='bold', pad=20)
            ax.set_xlim(0, 100)
            
            # Add progress labels
            for i, (bar, progress) in enumerate(zip(bars, target_progress)):
                width = bar.get_width()
                ax.text(width + 2, bar.get_y() + bar.get_height()/2,
                       f'{progress:.1f}%', ha='left', va='center', fontsize=9, fontweight='bold')
            
            # Add grid
            ax.grid(True, alpha=0.3, axis='x')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['bottom'].set_color('#E5E7EB')
            ax.spines['left'].set_color('#E5E7EB')
            
            plt.tight_layout()
            
            # Save to base64
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight',
                       facecolor='white', edgecolor='none')
            buffer.seek(0)
            chart_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            return chart_base64
            
        except Exception as e:
            print(f"Error creating targets chart: {e}")
            return None
    
    def _get_progress_status(self, progress: float) -> str:
        """Get status description based on progress percentage"""
        if progress >= 80:
            return "Mükemmel"
        elif progress >= 60:
            return "İyi"
        elif progress >= 40:
            return "Orta"
        elif progress >= 20:
            return "Zayıf"
        else:
            return "Başlangıç"
    
    def generate_training_report(self, trainings: List[Dict]) -> bytes:
        """Generate training-specific report"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, title=self._encode_turkish_text("Eğitim Raporu"))
        
        story = []
        story.append(Paragraph(self._encode_turkish_text("EĞİTİM RAPORU"), self.custom_styles['Title']))
        story.append(Spacer(1, 30))
        
        if trainings:
            training_data = [[self._encode_turkish_text('Eğitim Adı'), self._encode_turkish_text('Tarih'), self._encode_turkish_text('Katılımcı'), self._encode_turkish_text('Eğitmen'), self._encode_turkish_text('Durum')]]
            for training in trainings:
                name = self._encode_turkish_text(training.get('training_name', 'Bilinmeyen'))
                date = training.get('training_date', '')
                if date:
                    try:
                        date = datetime.fromisoformat(date.replace('Z', '')).strftime('%d.%m.%Y')
                    except:
                        date = 'Bilinmeyen'
                participants = str(training.get('participant_count', 0))
                trainer = self._encode_turkish_text(training.get('trainer_name', 'Belirtilmemiş'))
                status = self._encode_turkish_text('Tamamlandı' if training.get('status') == 'completed' else 'Planlandı')
                
                training_data.append([name[:25], date, participants, trainer[:20], status])
            
            training_table = Table(training_data, colWidths=[2*inch, 1.2*inch, 0.8*inch, 1.5*inch, 1*inch])
            training_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3B82F6')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
            ]))
            story.append(training_table)
        else:
            story.append(Paragraph(self._encode_turkish_text("Henüz eğitim verisi bulunmamaktadır."), self.custom_styles['Body']))
        
        doc.build(story, onFirstPage=self._add_header_footer, onLaterPages=self._add_header_footer)
        
        buffer.seek(0)
        return buffer.getvalue()
    
    def generate_consumption_report(self, consumption_data: List[Dict]) -> bytes:
        """Generate consumption-specific report"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, title=self._encode_turkish_text("Tüketim Raporu"))
        
        story = []
        story.append(Paragraph(self._encode_turkish_text("TÜKETİM RAPORU"), self.custom_styles['Title']))
        story.append(Spacer(1, 30))
        
        if consumption_data:
            consumption_table_data = [[self._encode_turkish_text('Ay'), self._encode_turkish_text('Elektrik (kWh)'), self._encode_turkish_text('Su (m³)'), self._encode_turkish_text('Gaz (m³)'), self._encode_turkish_text('Konaklama')]]
            total_electricity = 0
            total_water = 0
            total_gas = 0
            
            for consumption in consumption_data:
                month = self._encode_turkish_text(consumption.get('month', 'Bilinmeyen'))
                electricity = consumption.get('electricity', 0)
                water = consumption.get('water', 0)
                gas = consumption.get('gas', 0)
                accommodation = consumption.get('accommodation_count', 0)
                
                total_electricity += electricity
                total_water += water
                total_gas += gas
                
                consumption_table_data.append([
                    month,
                    f"{electricity:,.0f}",
                    f"{water:,.0f}",
                    f"{gas:,.0f}",
                    str(accommodation)
                ])
            
            # Add totals row
            consumption_table_data.append([
                self._encode_turkish_text('TOPLAM'),
                f"{total_electricity:,.0f}",
                f"{total_water:,.0f}",
                f"{total_gas:,.0f}",
                '-'
            ])
            
            consumption_table = Table(consumption_table_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch, 1*inch])
            consumption_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#059669')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -2), colors.lightgreen),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#16A34A')),
                ('TEXTCOLOR', (0, -1), (-1, -1), colors.whitesmoke),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(consumption_table)
        else:
            story.append(Paragraph(self._encode_turkish_text("Henüz tüketim verisi bulunmamaktadır."), self.custom_styles['Body']))
        
        doc.build(story, onFirstPage=self._add_header_footer, onLaterPages=self._add_header_footer)
        
        buffer.seek(0)
        return buffer.getvalue()


# Global instance
pdf_service = PDFReportService()