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
        Generate comprehensive report for a client
        Includes all data: consumption, trainings, personnel, suppliers, targets
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
        
        # Title Page
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
        
        # Executive Summary
        story.append(Paragraph(self._encode_turkish_text("YÖNETİCİ ÖZETİ"), self.custom_styles['Header']))
        
        stats = client_data.get('statistics', {})
        summary_data = [
            [self._encode_turkish_text('Metrik'), self._encode_turkish_text('Değer')],
            [self._encode_turkish_text('Toplam Belge Sayısı'), str(stats.get('total_documents', 0))],
            [self._encode_turkish_text('Toplam Eğitim Sayısı'), str(stats.get('total_trainings', 0))],
            [self._encode_turkish_text('Tamamlanan Eğitim'), str(stats.get('completed_trainings', 0))],
            [self._encode_turkish_text('Personel Sayısı'), str(stats.get('total_personnel', 0))],
            [self._encode_turkish_text('Tedarikçi Sayısı'), str(stats.get('total_suppliers', 0))]
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#059669')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 30))
        
        # Sustainability Progress
        story.append(Paragraph(self._encode_turkish_text("SÜRDÜRÜLEBİLİRLİK İLERLEMESİ"), self.custom_styles['Header']))
        
        sustainability = client_data.get('sustainability_progress', {})
        progress_data = [
            [self._encode_turkish_text('Alan'), self._encode_turkish_text('İlerleme (%)'), self._encode_turkish_text('Durum')],
            [self._encode_turkish_text('Karbon Azaltma'), f"{sustainability.get('carbon_reduction', 0)}%", self._encode_turkish_text(self._get_progress_status(sustainability.get('carbon_reduction', 0)))],
            [self._encode_turkish_text('Enerji Verimliliği'), f"{sustainability.get('energy_efficiency', 0)}%", self._encode_turkish_text(self._get_progress_status(sustainability.get('energy_efficiency', 0)))],
            [self._encode_turkish_text('Atık Azaltma'), f"{sustainability.get('waste_reduction', 0)}%", self._encode_turkish_text(self._get_progress_status(sustainability.get('waste_reduction', 0)))],
            [self._encode_turkish_text('Su Tasarrufu'), f"{sustainability.get('water_saving', 0)}%", self._encode_turkish_text(self._get_progress_status(sustainability.get('water_saving', 0)))]
        ]
        
        progress_table = Table(progress_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch])
        progress_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3B82F6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(progress_table)
        story.append(PageBreak())
        
        # Consumption Data
        story.append(Paragraph(self._encode_turkish_text("TÜKETİM VERİLERİ"), self.custom_styles['Header']))
        
        consumption = client_data.get('consumption_data', {})
        energy_data = consumption.get('energy_by_month', {})
        water_data = consumption.get('water_by_month', {})
        
        if energy_data or water_data:
            consumption_data = [[self._encode_turkish_text('Ay'), self._encode_turkish_text('Enerji (kWh)'), self._encode_turkish_text('Su (m³)')]]
            months = set(list(energy_data.keys()) + list(water_data.keys()))
            
            for month in sorted(months):
                energy = energy_data.get(month, 0)
                water = water_data.get(month, 0)
                consumption_data.append([self._encode_turkish_text(month), f"{energy:,.0f}", f"{water:,.0f}"])
            
            if len(consumption_data) > 1:  # Has data beyond headers
                consumption_table = Table(consumption_data, colWidths=[2*inch, 2*inch, 2*inch])
                consumption_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8B5CF6')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 11),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.lavender),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(consumption_table)
        else:
            story.append(Paragraph(self._encode_turkish_text("Henüz tüketim verisi bulunmamaktadır."), self.custom_styles['Body']))
        
        story.append(Spacer(1, 30))
        
        # Training Information
        if 'trainings' in client_data and len(client_data['trainings']) > 0:
            story.append(Paragraph(self._encode_turkish_text("EĞİTİM BİLGİLERİ"), self.custom_styles['Header']))
            
            training_data = [[self._encode_turkish_text('Eğitim Adı'), self._encode_turkish_text('Tarih'), self._encode_turkish_text('Katılımcı'), self._encode_turkish_text('Durum')]]
            for training in client_data['trainings'][:10]:  # Show latest 10
                name = self._encode_turkish_text(training.get('training_name', 'Bilinmeyen'))
                date = training.get('training_date', '')
                if date:
                    try:
                        date = datetime.fromisoformat(date.replace('Z', '')).strftime('%d.%m.%Y')
                    except:
                        date = 'Bilinmeyen'
                participants = training.get('participant_count', 0)
                status = self._encode_turkish_text('Tamamlandı' if training.get('status') == 'completed' else 'Planlandı')
                training_data.append([name[:30], date, str(participants), status])
            
            if len(training_data) > 1:
                training_table = Table(training_data, colWidths=[2.5*inch, 1.5*inch, 1*inch, 1*inch])
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
        
        # Recommendations
        if 'recommendations' in client_data and len(client_data['recommendations']) > 0:
            story.append(Paragraph(self._encode_turkish_text("ÖNERİLER"), self.custom_styles['Header']))
            
            for i, rec in enumerate(client_data['recommendations'][:5], 1):
                title = self._encode_turkish_text(rec.get('title', 'Öneri'))
                description = self._encode_turkish_text(rec.get('description', 'Açıklama yok'))
                priority = self._encode_turkish_text(rec.get('priority', 'Orta'))
                
                story.append(Paragraph(self._encode_turkish_text(f"{i}. {title} ({priority} Öncelik)"), self.custom_styles['Body']))
                story.append(Paragraph(self._encode_turkish_text(f"   {description}"), self.custom_styles['Body']))
                story.append(Spacer(1, 10))
        
        # Build PDF
        doc.build(story, onFirstPage=self._add_header_footer, onLaterPages=self._add_header_footer)
        
        buffer.seek(0)
        return buffer.getvalue()
    
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