"""
Elite PDF Report Generation Service for Rota-CRM
Premium professional reporting system with advanced design and analytics
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, Image as RLImage
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics import renderPDF
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import io
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend
import base64
from io import BytesIO
import pandas as pd
import numpy as np

class ElitePDFReportService:
    """
    Elite PDF Report Generation Service
    Premium professional reporting with advanced design, branding and analytics
    """
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        
        # Initialize brand colors FIRST - before font registration that might fail
        self.brand_colors = self._define_brand_colors()
        
        # Safe font registration with fallback
        try:
            self._register_turkish_fonts()
        except Exception as e:
            print(f"❌ Elite PDF: Font registration failed: {e}")
            print("🔄 Using Helvetica fallback")
            self.default_font = 'Helvetica'
            self.bold_font = 'Helvetica-Bold'
            self.use_character_replacement = True
        
        # Initialize styles after fonts are ready
        self.custom_styles = self._create_elite_styles()
        self.page_width = A4[0]
        self.page_height = A4[1]
    
    def _register_turkish_fonts(self):
        """Register Turkish-compatible Liberation fonts with full Unicode support"""
        import os
        
        # Liberation fonts - much more reliable than DejaVu for Turkish
        liberation_regular = '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf'
        liberation_bold = '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf'
        
        # Check Liberation fonts first (preferred)
        if os.path.exists(liberation_regular) and os.path.exists(liberation_bold):
            # Register Liberation fonts
            pdfmetrics.registerFont(TTFont('LiberationSans', liberation_regular))
            pdfmetrics.registerFont(TTFont('LiberationSans-Bold', liberation_bold))
            
            # Register font family mappings
            from reportlab.lib.fonts import addMapping
            addMapping('LiberationSans', 0, 0, 'LiberationSans')        # normal
            addMapping('LiberationSans', 1, 0, 'LiberationSans-Bold')  # bold
            addMapping('LiberationSans', 0, 1, 'LiberationSans')       # italic (use regular)
            addMapping('LiberationSans', 1, 1, 'LiberationSans-Bold')  # bold+italic
            
            self.default_font = 'LiberationSans'
            self.bold_font = 'LiberationSans-Bold'
            
            print("✅ Elite PDF: Liberation Sans fonts registered - FULL Turkish Unicode support")
            
            # Test Turkish characters
            test_chars = "ğüşıöçĞÜŞİÖÇ"
            print(f"✅ Turkish character test: {test_chars}")
            
        else:
            # Fallback to DejaVu if available
            dejavu_regular = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
            dejavu_bold = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
            
            if os.path.exists(dejavu_regular) and os.path.exists(dejavu_bold):
                pdfmetrics.registerFont(TTFont('DejaVuSans', dejavu_regular))
                pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', dejavu_bold))
                
                from reportlab.lib.fonts import addMapping
                addMapping('DejaVuSans', 0, 0, 'DejaVuSans')       
                addMapping('DejaVuSans', 1, 0, 'DejaVuSans-Bold')  
                addMapping('DejaVuSans', 0, 1, 'DejaVuSans')       
                addMapping('DejaVuSans', 1, 1, 'DejaVuSans-Bold')  
                
                self.default_font = 'DejaVuSans'
                self.bold_font = 'DejaVuSans-Bold'
                
                print("✅ Elite PDF: DejaVu fonts registered as fallback")
            else:
                raise Exception(f"Neither Liberation nor DejaVu fonts found - Turkish characters may not render correctly")
    
    def _create_elite_styles(self):
        """Create elite custom styles for premium reporting"""
        elite_styles = {}
        
        # Elite Title style with gradient effect simulation
        elite_styles['Title'] = ParagraphStyle(
            'EliteTitle',
            parent=self.styles['Title'],
            fontSize=32,
            spaceAfter=40,
            alignment=TA_CENTER,
            textColor=self.brand_colors.get('primary', colors.HexColor('#059669')),
            fontName=self.bold_font,
            leading=40
        )
        
        # Elite Cover Title - even bigger for cover page
        elite_styles['CoverTitle'] = ParagraphStyle(
            'EliteCoverTitle',
            parent=self.styles['Title'],
            fontSize=36,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=self.brand_colors.get('secondary', colors.HexColor('#1a365d')),
            fontName=self.bold_font,
            leading=44
        )
        
        # Elite Subtitle with enhanced styling
        elite_styles['Subtitle'] = ParagraphStyle(
            'EliteSubtitle',
            parent=self.styles['Heading2'],
            fontSize=20,
            spaceAfter=25,
            textColor=self.brand_colors.get('dark', colors.HexColor('#2d3748')),
            fontName=self.bold_font,
            alignment=TA_CENTER,
            leading=26
        )
        
        # Elite Header with premium styling
        elite_styles['Header'] = ParagraphStyle(
            'EliteHeader',
            parent=self.styles['Heading3'],
            fontSize=18,
            spaceAfter=20,
            spaceBefore=15,
            textColor=self.brand_colors.get('primary', colors.HexColor('#059669')),
            fontName=self.bold_font,
            leftIndent=0,
            leading=22
        )
        
        # Elite Section Header
        elite_styles['SectionHeader'] = ParagraphStyle(
            'EliteSectionHeader',
            parent=self.styles['Heading3'],
            fontSize=16,
            spaceAfter=15,
            spaceBefore=10,
            textColor=self.brand_colors.get('secondary', colors.HexColor('#1a365d')),
            fontName=self.bold_font,
            leftIndent=0,
            leading=20
        )
        
        # Elite Body with enhanced readability
        elite_styles['Body'] = ParagraphStyle(
            'EliteBody',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=12,
            leading=16,
            fontName=self.default_font,
            textColor=self.brand_colors.get('dark', colors.HexColor('#2d3748')),
            leftIndent=0,
            rightIndent=0,
            alignment=TA_JUSTIFY
        )
        
        # Elite Executive Summary style
        elite_styles['Executive'] = ParagraphStyle(
            'EliteExecutive',
            parent=self.styles['Normal'],
            fontSize=12,
            spaceAfter=15,
            leading=18,
            fontName=self.default_font,
            textColor=self.brand_colors.get('dark', colors.HexColor('#2d3748')),
            leftIndent=20,
            rightIndent=20,
            alignment=TA_JUSTIFY,
            backColor=self.brand_colors.get('light', colors.HexColor('#f7fafc'))
        )
        
        # Elite Highlight style for KPIs
        elite_styles['KPI'] = ParagraphStyle(
            'EliteKPI',
            parent=self.styles['Normal'],
            fontSize=14,
            spaceAfter=10,
            leading=18,
            fontName=self.bold_font,
            textColor=self.brand_colors.get('primary', colors.HexColor('#059669')),
            alignment=TA_CENTER
        )
        
        # Elite Quote style for recommendations
        elite_styles['Quote'] = ParagraphStyle(
            'EliteQuote',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=15,
            leading=16,
            fontName=self.default_font,
            textColor=self.brand_colors.get('dark', colors.HexColor('#2d3748')),
            leftIndent=30,
            rightIndent=30,
            alignment=TA_JUSTIFY,
            backColor=self.brand_colors.get('light', colors.HexColor('#f7fafc'))
        )
        
        return elite_styles
    
    def _define_brand_colors(self):
        """Define elite brand color palette"""
        return {
            'primary': colors.HexColor('#059669'),      # Emerald green
            'secondary': colors.HexColor('#1a365d'),    # Dark blue
            'accent': colors.HexColor('#3182ce'),       # Blue
            'success': colors.HexColor('#38a169'),      # Green
            'warning': colors.HexColor('#d69e2e'),      # Orange
            'danger': colors.HexColor('#e53e3e'),       # Red
            'info': colors.HexColor('#3182ce'),         # Blue
            'light': colors.HexColor('#f7fafc'),        # Light gray
            'dark': colors.HexColor('#2d3748'),         # Dark gray
            'muted': colors.HexColor('#718096'),        # Muted gray
            'background': colors.HexColor('#ffffff'),   # White
            'border': colors.HexColor('#e2e8f0')        # Light border
        }
    
    def _encode_turkish_text(self, text):
        """Handle Turkish characters - NO CONVERSION NEEDED with Liberation/DejaVu fonts"""
        if not text:
            return ""
        
        try:
            # With proper Unicode fonts (Liberation/DejaVu), keep ALL Turkish characters as-is
            # Liberation Sans has FULL Unicode support for Turkish: ğüşıöçĞÜŞİÖÇ
            if hasattr(self, 'use_character_replacement') and self.use_character_replacement:
                # Only use replacement if we fell back to Helvetica
                char_map = {
                    'ğ': 'g', 'Ğ': 'G',
                    'ü': 'u', 'Ü': 'U', 
                    'ö': 'o', 'Ö': 'O',
                    'ş': 's', 'Ş': 'S',
                    'ç': 'c', 'Ç': 'C',
                    'ı': 'i', 'İ': 'I'
                }
                
                result = str(text)
                for turkish_char, ascii_char in char_map.items():
                    result = result.replace(turkish_char, ascii_char)
                return result
            else:
                # With Liberation/DejaVu font, keep Turkish characters exactly as-is
                # Full Unicode support - no conversion needed!
                return str(text)
                
        except Exception as e:
            print(f"Error handling Turkish text: {e}")
            return str(text)
    
    def _add_watermark(self, canvas, doc):
        """Add watermark to the page"""
        canvas.saveState()
        canvas.setFillColor(colors.HexColor('#f7fafc'))
        canvas.setFillAlpha(0.1)
        canvas.setFont(self.bold_font, 60)
        
        # Rotate and add watermark text
        canvas.rotate(45)
        canvas.drawString(200, -200, self._encode_turkish_text("ROTA KALİTE"))
        canvas.restoreState()
    
    def _add_elite_header_footer(self, canvas, doc):
        """Add elite header and footer to each page"""
        canvas.saveState()
        
        # Header section with gradient effect simulation
        header_height = 80
        
        # Header background rectangle
        canvas.setFillColor(self.brand_colors['primary'])
        canvas.rect(0, self.page_height - header_height, self.page_width, header_height, fill=1, stroke=0)
        
        # Company logo area (simulated)
        canvas.setFillColor(colors.white)
        canvas.rect(30, self.page_height - 65, 50, 35, fill=1, stroke=0)
        
        # Company name
        canvas.setFont(self.bold_font, 24)
        canvas.setFillColor(colors.white)
        canvas.drawString(100, self.page_height - 45, self._encode_turkish_text("ROTA KALİTE"))
        
        canvas.setFont(self.default_font, 12)
        canvas.drawString(100, self.page_height - 60, self._encode_turkish_text("& DANIŞMANLIK"))
        
        # Report date
        canvas.setFont(self.default_font, 10)
        canvas.drawRightString(self.page_width - 30, self.page_height - 35, 
                             f"Rapor Tarihi: {datetime.now().strftime('%d.%m.%Y')}")
        canvas.drawRightString(self.page_width - 30, self.page_height - 50, 
                             f"Saat: {datetime.now().strftime('%H:%M')}")
        
        # Footer section
        footer_height = 60
        
        # Footer background
        canvas.setFillColor(self.brand_colors['light'])
        canvas.rect(0, 0, self.page_width, footer_height, fill=1, stroke=0)
        
        # Footer line
        canvas.setStrokeColor(self.brand_colors['primary'])
        canvas.setLineWidth(2)
        canvas.line(30, footer_height - 10, self.page_width - 30, footer_height - 10)
        
        # Footer text
        canvas.setFont(self.default_font, 9)
        canvas.setFillColor(self.brand_colors['dark'])
        canvas.drawString(30, 35, self._encode_turkish_text("Bu rapor Rota-CRM Premium sistemi tarafından"))
        canvas.drawString(30, 25, self._encode_turkish_text("otomatik olarak üretilmiştir."))
        canvas.drawString(30, 15, self._encode_turkish_text("© 2025 ROTA Kalite & Danışmanlık - Tüm hakları saklıdır."))
        
        # Page number with premium styling
        canvas.setFont(self.bold_font, 11)
        canvas.setFillColor(self.brand_colors['primary'])
        page_text = f"Sayfa {doc.page}"
        canvas.drawRightString(self.page_width - 30, 25, page_text)
        
        # Add watermark
        self._add_watermark(canvas, doc)
        
        canvas.restoreState()
    
    def _create_cover_page(self, client_data: Dict) -> List:
        """Create elite cover page"""
        cover_elements = []
        
        # Add spacer for header
        cover_elements.append(Spacer(1, 100))
        
        # Main title with enhanced styling
        cover_elements.append(Paragraph(
            self._encode_turkish_text("SÜRDÜRÜLEBİLİRLİK"),
            self.custom_styles['CoverTitle']
        ))
        cover_elements.append(Paragraph(
            self._encode_turkish_text("PERFORMANS RAPORU"),
            self.custom_styles['CoverTitle']
        ))
        
        cover_elements.append(Spacer(1, 50))
        
        # Client information box
        hotel_name = client_data.get('client_info', {}).get('hotel_name') or client_data.get('client_info', {}).get('name', 'Bilinmeyen')
        city = client_data.get('client_info', {}).get('city', 'Türkiye')
        
        cover_elements.append(Paragraph(
            self._encode_turkish_text(f"<b>{hotel_name}</b>"),
            self.custom_styles['Subtitle']
        ))
        cover_elements.append(Paragraph(
            self._encode_turkish_text(f"{city}"),
            self.custom_styles['Body']
        ))
        
        cover_elements.append(Spacer(1, 80))
        
        # Report period and type
        current_date = datetime.now().strftime('%d %B %Y')
        
        report_info_data = [
            [self._encode_turkish_text("Rapor Türü:"), self._encode_turkish_text("Premium Sürdürülebilirlik Analizi")],
            [self._encode_turkish_text("Rapor Dönemi:"), self._encode_turkish_text(f"2024 Yıl Sonu - {current_date}")],
            [self._encode_turkish_text("Rapor Versiyonu:"), "Elite v2.0"],
            [self._encode_turkish_text("Hazırlanan:"), self._encode_turkish_text("ROTA Kalite & Danışmanlık")]
        ]
        
        report_info_table = Table(report_info_data, colWidths=[2*inch, 3*inch])
        report_info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), self.brand_colors['light']),
            ('TEXTCOLOR', (0, 0), (-1, -1), self.brand_colors['dark']),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), self.bold_font),
            ('FONTNAME', (1, 0), (1, -1), self.default_font),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 15),
            ('RIGHTPADDING', (0, 0), (-1, -1), 15),
            ('GRID', (0, 0), (-1, -1), 1, self.brand_colors['border']),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
        ]))
        
        cover_elements.append(report_info_table)
        cover_elements.append(Spacer(1, 60))
        
        # Executive summary preview
        cover_elements.append(Paragraph(
            self._encode_turkish_text("RAPOR ÖZETİ"),
            self.custom_styles['Header']
        ))
        
        stats = client_data.get('statistics', {})
        summary_text = f"""Bu premium rapor, {hotel_name} işletmesinin sürdürülebilirlik performansını 
        detaylı analiz etmektedir. Raporda {stats.get('total_documents', 0)} belge, 
        {stats.get('total_trainings', 0)} eğitim, {stats.get('total_personnel', 0)} personel ve 
        {stats.get('total_suppliers', 0)} tedarikçi verisi analiz edilmiştir. Gelişmiş görsel 
        analizler ve stratejik öneriler içermektedir."""
        
        cover_elements.append(Paragraph(
            self._encode_turkish_text(summary_text),
            self.custom_styles['Executive']
        ))
        
        cover_elements.append(PageBreak())
        return cover_elements
    
    def _create_executive_summary(self, client_data: Dict) -> List:
        """Create executive summary with KPIs"""
        elements = []
        
        elements.append(Paragraph(
            self._encode_turkish_text("YÖNETİCİ ÖZETİ"),
            self.custom_styles['Title']
        ))
        elements.append(Spacer(1, 30))
        
        # KPI Dashboard
        stats = client_data.get('statistics', {})
        sustainability = client_data.get('sustainability_progress', {})
        
        # Key metrics table
        kpi_data = [
            [self._encode_turkish_text('Performans Göstergesi'), self._encode_turkish_text('Mevcut Değer'), self._encode_turkish_text('Hedef'), self._encode_turkish_text('Durum')],
            [self._encode_turkish_text('Sürdürülebilirlik Skoru'), f"{(sustainability.get('carbon_reduction', 0) + sustainability.get('energy_efficiency', 0))/2:.1f}%", "75%", self._encode_turkish_text("İYİ")],
            [self._encode_turkish_text('Belge Tamamlama'), f"{stats.get('total_documents', 0)}", "25", self._encode_turkish_text("MÜKEMMEL" if stats.get('total_documents', 0) >= 25 else "İYİ")],
            [self._encode_turkish_text('Eğitim Etkinliği'), f"{(stats.get('completed_trainings', 0)/max(1, stats.get('total_trainings', 1))*100):.1f}%", "90%", self._encode_turkish_text("İYİ")],
            [self._encode_turkish_text('Personel Katılımı'), f"{stats.get('total_personnel', 0)}", "30", self._encode_turkish_text("İYİ" if stats.get('total_personnel', 0) >= 20 else "ORTA")]
        ]
        
        kpi_table = Table(kpi_data, colWidths=[2.5*inch, 1.2*inch, 1*inch, 1.3*inch])
        kpi_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.brand_colors['primary']),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), self.bold_font),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (0, 1), (-1, -1), self.brand_colors['light']),
            ('GRID', (0, 0), (-1, -1), 1, self.brand_colors['border']),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
        ]))
        
        elements.append(kpi_table)
        elements.append(Spacer(1, 30))
        
        # Executive insights
        elements.append(Paragraph(
            self._encode_turkish_text("STRATEJİK DEĞERLENDİRME"),
            self.custom_styles['Header']
        ))
        
        insights = f"""
        İşletmenizin sürdürülebilirlik performansı analiz edildiğinde, güçlü yanlarınız ve 
        gelişim alanlarınız net bir şekilde ortaya çıkmaktadır. Özellikle belge yönetimi 
        konusunda {stats.get('total_documents', 0)} belge ile başarılı bir performans 
        sergilenmekte, personel eğitimi alanında ise {stats.get('completed_trainings', 0)} 
        tamamlanan eğitim ile sektör ortalamasının üzerinde yer almaktasınız.
        
        Sürdürülebilirlik hedeflerinize ulaşmak için önerdiğimiz öncelikli aksiyonlar 
        aşağıdaki bölümlerde detaylandırılmıştır.
        """
        
        elements.append(Paragraph(
            self._encode_turkish_text(insights),
            self.custom_styles['Executive']
        ))
        
        elements.append(PageBreak())
        return elements
    
    def generate_comprehensive_report(self, client_data: Dict, report_type: str = "comprehensive") -> bytes:
        """
        Generate elite comprehensive report with premium design and advanced analytics
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=50,
            leftMargin=50,
            topMargin=120,
            bottomMargin=80,
            title=self._encode_turkish_text("Elite Sürdürülebilirlik Raporu"),
            author="ROTA Kalite & Danışmanlık",
            subject="Sürdürülebilirlik Performans Analizi"
        )
        
        # Build the story (content)
        story = []
        
        # COVER PAGE
        story.extend(self._create_cover_page(client_data))
        
        # EXECUTIVE SUMMARY
        story.extend(self._create_executive_summary(client_data))
        
        # SUSTAINABILITY PROGRESS WITH ENHANCED VISUALS
        story.append(Paragraph(
            self._encode_turkish_text("SÜRDÜRÜLEBİLİRLİK PERFORMANSI"),
            self.custom_styles['Title']
        ))
        
        # Add enhanced sustainability progress chart
        sustainability = client_data.get('sustainability_progress', {})
        sustain_chart = self._create_elite_sustainability_chart(sustainability)
        if sustain_chart:
            from reportlab.platypus import Image
            chart_img = Image(io.BytesIO(base64.b64decode(sustain_chart)), width=6.5*inch, height=5*inch)
            story.append(chart_img)
            story.append(Spacer(1, 20))
        
        # Enhanced progress details
        progress_data = [
            [self._encode_turkish_text('Sürdürülebilirlik Alanı'), self._encode_turkish_text('İlerleme'), self._encode_turkish_text('Hedef'), self._encode_turkish_text('Performans')],
            [self._encode_turkish_text('Karbon Emisyon Azaltma'), f"{sustainability.get('carbon_reduction', 0):.1f}%", "25%", self._get_elite_status(sustainability.get('carbon_reduction', 0))],
            [self._encode_turkish_text('Enerji Verimliliği'), f"{sustainability.get('energy_efficiency', 0):.1f}%", "30%", self._get_elite_status(sustainability.get('energy_efficiency', 0))],
            [self._encode_turkish_text('Atık Azaltma'), f"{sustainability.get('waste_reduction', 0):.1f}%", "20%", self._get_elite_status(sustainability.get('waste_reduction', 0))],
            [self._encode_turkish_text('Su Tasarrufu'), f"{sustainability.get('water_saving', 0):.1f}%", "15%", self._get_elite_status(sustainability.get('water_saving', 0))]
        ]
        
        progress_table = Table(progress_data, colWidths=[2.8*inch, 1.2*inch, 1*inch, 1*inch])
        progress_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.brand_colors['secondary']),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), self.bold_font),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
            ('TOPPADDING', (0, 0), (-1, -1), 15),
            ('BACKGROUND', (0, 1), (-1, -1), self.brand_colors['light']),
            ('GRID', (0, 0), (-1, -1), 1, self.brand_colors['border']),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
        ]))
        
        story.append(progress_table)
        story.append(PageBreak())
        
        # CONSUMPTION ANALYSIS - Enhanced
        story.append(Paragraph(
            self._encode_turkish_text("TÜKETİM ANALİZİ VE TRENDLERİ"),
            self.custom_styles['Title']
        ))
        
        consumption = client_data.get('consumption_data', {})
        energy_data = consumption.get('energy_by_month', {})
        water_data = consumption.get('water_by_month', {})
        
        # Enhanced consumption chart
        consumption_chart = self._create_elite_consumption_chart(energy_data, water_data)
        if consumption_chart:
            from reportlab.platypus import Image
            chart_img = Image(io.BytesIO(base64.b64decode(consumption_chart)), width=6.5*inch, height=4*inch)
            story.append(chart_img)
            story.append(Spacer(1, 20))
        
        # Consumption analysis table
        if energy_data or water_data:
            total_energy = sum(energy_data.values()) if energy_data else 0
            total_water = sum(water_data.values()) if water_data else 0
            
            consumption_analysis = [
                [self._encode_turkish_text('Tüketim Analizi'), self._encode_turkish_text('Değer'), self._encode_turkish_text('Sektör Ort.'), self._encode_turkish_text('Performans')],
                [self._encode_turkish_text('Toplam Enerji'), f"{total_energy:,.0f} kWh", "180,000 kWh", self._encode_turkish_text("İyi" if total_energy < 180000 else "Orta")],
                [self._encode_turkish_text('Toplam Su'), f"{total_water:,.0f} m³", "15,000 m³", self._encode_turkish_text("İyi" if total_water < 15000 else "Orta")],
                [self._encode_turkish_text('Enerji Verimliliği'), f"{(total_energy/12):,.0f} kWh/ay", "15,000 kWh/ay", self._encode_turkish_text("Mükemmel")],
                [self._encode_turkish_text('Su Verimliliği'), f"{(total_water/12):,.0f} m³/ay", "1,250 m³/ay", self._encode_turkish_text("İyi")]
            ]
            
            consumption_table = Table(consumption_analysis, colWidths=[2.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
            consumption_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), self.brand_colors['accent']),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), self.bold_font),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
                ('TOPPADDING', (0, 0), (-1, -1), 15),
                ('BACKGROUND', (0, 1), (-1, -1), self.brand_colors['light']),
                ('GRID', (0, 0), (-1, -1), 1, self.brand_colors['border']),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
            ]))
            
            story.append(consumption_table)
        
        story.append(PageBreak())
        
        # RECOMMENDATIONS AND ACTION PLAN - Enhanced
        story.append(Paragraph(
            self._encode_turkish_text("STRATEJİK ÖNERİLER VE AKSİYON PLANI"),
            self.custom_styles['Title']
        ))
        
        # Priority recommendations with enhanced styling
        recommendations = [
            {
                'title': 'Enerji Yönetim Sistemi Kurulumu',
                'description': 'Akıllı enerji izleme sistemleri kurarak tüketimi %20 azaltabilirsiniz.',
                'priority': 'Yüksek',
                'timeline': '3 ay',
                'investment': 'Orta'
            },
            {
                'title': 'Personel Sürdürülebilirlik Eğitimi',
                'description': 'Tüm personele yönelik kapsamlı sürdürülebilirlik farkındalık programı.',
                'priority': 'Yüksek',
                'timeline': '2 ay',
                'investment': 'Düşük'
            },
            {
                'title': 'Tedarikçi Değerlendirme Sistemi',
                'description': 'Sürdürülebilir tedarikçi seçimi için değerlendirme kriterleri oluşturma.',
                'priority': 'Orta',
                'timeline': '4 ay',
                'investment': 'Düşük'
            }
        ]
        
        for i, rec in enumerate(recommendations, 1):
            # Create recommendation box
            rec_data = [
                [self._encode_turkish_text(f"ÖNERİ {i}: {rec['title']}")],
                [self._encode_turkish_text(rec['description'])],
                [self._encode_turkish_text(f"Öncelik: {rec['priority']} | Süre: {rec['timeline']} | Yatırım: {rec['investment']}")]
            ]
            
            rec_table = Table(rec_data, colWidths=[6*inch])
            rec_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), self.brand_colors['primary']),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), self.bold_font),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('LEFTPADDING', (0, 0), (-1, -1), 15),
                ('RIGHTPADDING', (0, 0), (-1, -1), 15),
                ('TOPPADDING', (0, 0), (-1, -1), 12),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('BACKGROUND', (0, 1), (-1, -1), self.brand_colors['light']),
                ('FONTSIZE', (0, 1), (-1, 1), 11),
                ('FONTSIZE', (0, 2), (-1, 2), 9),
                ('TEXTCOLOR', (0, 2), (-1, 2), self.brand_colors['muted']),
                ('GRID', (0, 0), (-1, -1), 1, self.brand_colors['border'])
            ]))
            
            story.append(rec_table)
            story.append(Spacer(1, 15))
        
        # Final conclusion
        story.append(Spacer(1, 30))
        story.append(Paragraph(
            self._encode_turkish_text("SONUÇ VE DEĞERLENDİRME"),
            self.custom_styles['Header']
        ))
        
        conclusion = f"""Bu elite rapor kapsamında gerçekleştirilen detaylı analizler sonucunda, 
        işletmenizin sürdürülebilirlik yolculuğunda önemli adımlar attığı görülmektedir. 
        Yukarıda belirtilen stratejik önerilerin uygulanması ile sektörde lider konuma 
        gelebilir ve çevresel etkilerinizi minimum seviyeye indirebilirsiniz.
        
        ROTA Kalite & Danışmanlık olarak, bu süreçte yanınızda olmaktan gurur duyarız."""
        
        story.append(Paragraph(
            self._encode_turkish_text(conclusion),
            self.custom_styles['Quote']
        ))
        
        # Build PDF with elite styling
        doc.build(story, onFirstPage=self._add_elite_header_footer, onLaterPages=self._add_elite_header_footer)
        
        buffer.seek(0)
        return buffer.getvalue()
    
    def _create_elite_sustainability_chart(self, sustainability_data: dict) -> str:
        """Create elite sustainability progress chart with premium styling"""
        try:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 8))
            plt.style.use('seaborn-v0_8-whitegrid')
            
            # Left: Progress bars
            categories = ['Karbon\nAzaltma', 'Enerji\nVerimliliği', 'Atık\nAzaltma', 'Su\nTasarrufu']
            values = [
                sustainability_data.get('carbon_reduction', 0),
                sustainability_data.get('energy_efficiency', 0),
                sustainability_data.get('waste_reduction', 0),
                sustainability_data.get('water_saving', 0)
            ]
            
            # Create gradient colors
            colors_gradient = ['#ef4444', '#3b82f6', '#8b5cf6', '#06b6d4']
            
            bars = ax1.barh(categories, values, color=colors_gradient, alpha=0.8, height=0.6)
            ax1.set_xlim(0, 100)
            ax1.set_xlabel('İlerleme (%)', fontsize=12, fontweight='bold')
            ax1.set_title('Sürdürülebilirlik Hedefleri İlerleme', fontsize=14, fontweight='bold', pad=20)
            
            # Add percentage labels
            for i, (bar, value) in enumerate(zip(bars, values)):
                width = bar.get_width()
                ax1.text(width + 2, bar.get_y() + bar.get_height()/2,
                        f'{value:.1f}%', ha='left', va='center', fontweight='bold', fontsize=11)
            
            # Right: Donut chart
            wedges, texts, autotexts = ax2.pie(values, labels=categories, colors=colors_gradient, 
                                             autopct='%1.1f%%', startangle=90, pctdistance=0.85,
                                             textprops={'fontsize': 10, 'fontweight': 'bold'})
            
            # Center circle for donut
            centre_circle = plt.Circle((0,0), 0.70, fc='white', ec='#e2e8f0', linewidth=2)
            fig.gca().add_artist(centre_circle)
            
            ax2.set_title('Genel Sürdürülebilirlik Performansı', fontsize=14, fontweight='bold', pad=20)
            
            # Center text
            avg_progress = sum(values) / len(values)
            ax2.text(0, 0, f'Genel\nSkor\n{avg_progress:.1f}%', ha='center', va='center',
                    fontsize=12, fontweight='bold', color='#374151')
            
            plt.tight_layout()
            
            # Save with high quality
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight',
                       facecolor='white', edgecolor='none')
            buffer.seek(0)
            chart_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            return chart_base64
            
        except Exception as e:
            print(f"Error creating elite sustainability chart: {e}")
            return None
    
    def _create_elite_consumption_chart(self, energy_data: dict, water_data: dict) -> str:
        """Create elite consumption analysis chart"""
        try:
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))
            plt.style.use('seaborn-v0_8-whitegrid')
            
            # Energy consumption trend
            if energy_data:
                months = list(energy_data.keys())
                values = list(energy_data.values())
                
                ax1.plot(months, values, marker='o', linewidth=3, markersize=8, 
                        color='#3b82f6', markerfacecolor='#1d4ed8')
                ax1.fill_between(months, values, alpha=0.3, color='#3b82f6')
                ax1.set_title('Enerji Tüketimi Trendi', fontsize=12, fontweight='bold')
                ax1.set_ylabel('kWh', fontsize=10)
                ax1.tick_params(axis='x', rotation=45)
                ax1.grid(True, alpha=0.3)
                
                # Add trend line
                if len(values) > 1:
                    z = np.polyfit(range(len(values)), values, 1)
                    p = np.poly1d(z)
                    ax1.plot(months, p(range(len(values))), "--", color='red', alpha=0.8, linewidth=2)
            else:
                ax1.text(0.5, 0.5, 'Enerji verisi\nmevcut değil', ha='center', va='center',
                        transform=ax1.transAxes, fontsize=12)
                ax1.set_title('Enerji Tüketimi', fontsize=12, fontweight='bold')
            
            # Water consumption trend  
            if water_data:
                months = list(water_data.keys())
                values = list(water_data.values())
                
                ax2.plot(months, values, marker='s', linewidth=3, markersize=8,
                        color='#06b6d4', markerfacecolor='#0891b2')
                ax2.fill_between(months, values, alpha=0.3, color='#06b6d4')
                ax2.set_title('Su Tüketimi Trendi', fontsize=12, fontweight='bold')
                ax2.set_ylabel('m³', fontsize=10)
                ax2.tick_params(axis='x', rotation=45)
                ax2.grid(True, alpha=0.3)
                
                # Add trend line
                if len(values) > 1:
                    z = np.polyfit(range(len(values)), values, 1)
                    p = np.poly1d(z)
                    ax2.plot(months, p(range(len(values))), "--", color='red', alpha=0.8, linewidth=2)
            else:
                ax2.text(0.5, 0.5, 'Su verisi\nmevcut değil', ha='center', va='center',
                        transform=ax2.transAxes, fontsize=12)
                ax2.set_title('Su Tüketimi', fontsize=12, fontweight='bold')
            
            # Energy efficiency comparison
            if energy_data and len(energy_data) >= 2:
                months = list(energy_data.keys())[-6:]  # Last 6 months
                values = list(energy_data.values())[-6:]
                efficiency = [max(0, 100 - (v/max(values))*100) for v in values]
                
                ax3.bar(months, efficiency, color='#10b981', alpha=0.8)
                ax3.set_title('Enerji Verimliliği İndeksi', fontsize=12, fontweight='bold')
                ax3.set_ylabel('Verimlilik %', fontsize=10)
                ax3.tick_params(axis='x', rotation=45)
                ax3.set_ylim(0, 100)
            else:
                ax3.text(0.5, 0.5, 'Verimlilik\nanalizi için\nyeterli veri yok', 
                        ha='center', va='center', transform=ax3.transAxes, fontsize=10)
                ax3.set_title('Enerji Verimliliği', fontsize=12, fontweight='bold')
            
            # Combined consumption comparison
            if energy_data and water_data:
                months = list(set(energy_data.keys()) & set(water_data.keys()))[:6]
                energy_vals = [energy_data.get(m, 0) for m in months]
                water_vals = [water_data.get(m, 0) * 10 for m in months]  # Scale water for comparison
                
                x = np.arange(len(months))
                width = 0.35
                
                ax4.bar(x - width/2, energy_vals, width, label='Enerji (kWh)', color='#3b82f6', alpha=0.8)
                ax4.bar(x + width/2, water_vals, width, label='Su (m³ x10)', color='#06b6d4', alpha=0.8)
                
                ax4.set_title('Enerji-Su Tüketimi Karşılaştırması', fontsize=12, fontweight='bold')
                ax4.set_ylabel('Tüketim Miktarı', fontsize=10)
                ax4.set_xticks(x)
                ax4.set_xticklabels(months, rotation=45)
                ax4.legend()
                ax4.grid(True, alpha=0.3, axis='y')
            else:
                ax4.text(0.5, 0.5, 'Karşılaştırma için\nyeterli veri yok', 
                        ha='center', va='center', transform=ax4.transAxes, fontsize=10)
                ax4.set_title('Tüketim Karşılaştırması', fontsize=12, fontweight='bold')
            
            plt.tight_layout()
            
            # Save with high quality
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight',
                       facecolor='white', edgecolor='none')
            buffer.seek(0)
            chart_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            return chart_base64
            
        except Exception as e:
            print(f"Error creating elite consumption chart: {e}")
            return None
    
    def _get_elite_status(self, value: float) -> str:
        """Get elite status description based on performance"""
        if value >= 90:
            return self._encode_turkish_text("🏆 MÜKEMMELy")
        elif value >= 75:
            return self._encode_turkish_text("⭐ ÇOK İYİ")
        elif value >= 60:
            return self._encode_turkish_text("✅ İYİ")
        elif value >= 40:
            return self._encode_turkish_text("⚠️ ORTA")
        elif value >= 20:
            return self._encode_turkish_text("🔺 ZAYIF")
        else:
            return self._encode_turkish_text("🔻 YETERSİZ")
    
    def generate_training_report(self, trainings: List[Dict]) -> bytes:
        """Generate elite training report"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=A4, 
            title=self._encode_turkish_text("Elite Eğitim Raporu"),
            topMargin=120,
            bottomMargin=80
        )
        
        story = []
        story.append(Paragraph(self._encode_turkish_text("ELİTE EĞİTİM RAPORU"), self.custom_styles['Title']))
        story.append(Spacer(1, 30))
        
        if trainings:
            # Enhanced training analysis
            completed = len([t for t in trainings if t.get('status') == 'completed'])
            completion_rate = (completed / len(trainings) * 100) if trainings else 0
            
            # Summary box
            summary_data = [
                [self._encode_turkish_text("Toplam Eğitim"), str(len(trainings))],
                [self._encode_turkish_text("Tamamlanan"), str(completed)],
                [self._encode_turkish_text("Başarı Oranı"), f"{completion_rate:.1f}%"],
                [self._encode_turkish_text("Durum"), self._get_elite_status(completion_rate)]
            ]
            
            summary_table = Table(summary_data, colWidths=[2*inch, 2*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), self.brand_colors['light']),
                ('TEXTCOLOR', (0, 0), (-1, -1), self.brand_colors['dark']),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (0, -1), self.bold_font),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
                ('TOPPADDING', (0, 0), (-1, -1), 15),
                ('GRID', (0, 0), (-1, -1), 1, self.brand_colors['border'])
            ]))
            
            story.append(summary_table)
            story.append(Spacer(1, 30))
            
            # Detailed training table
            training_data = [[
                self._encode_turkish_text('Eğitim Adı'), 
                self._encode_turkish_text('Tarih'), 
                self._encode_turkish_text('Katılımcı'), 
                self._encode_turkish_text('Eğitmen'), 
                self._encode_turkish_text('Durum')
            ]]
            
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
                status = self._encode_turkish_text('✅ Tamamlandı' if training.get('status') == 'completed' else '⏳ Planlandı')
                
                training_data.append([name[:30], date, participants, trainer[:20], status])
            
            training_table = Table(training_data, colWidths=[2.2*inch, 1*inch, 0.8*inch, 1.5*inch, 1.5*inch])
            training_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), self.brand_colors['primary']),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), self.bold_font),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('TOPPADDING', (0, 0), (-1, -1), 12),
                ('BACKGROUND', (0, 1), (-1, -1), self.brand_colors['light']),
                ('GRID', (0, 0), (-1, -1), 1, self.brand_colors['border']),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
            ]))
            story.append(training_table)
        else:
            story.append(Paragraph(
                self._encode_turkish_text("Henüz eğitim verisi bulunmamaktadır. Elite eğitim programı başlatılması önerilmektedir."), 
                self.custom_styles['Body']
            ))
        
        doc.build(story, onFirstPage=self._add_elite_header_footer, onLaterPages=self._add_elite_header_footer)
        
        buffer.seek(0)
        return buffer.getvalue()
    
    def generate_consumption_report(self, consumption_data: List[Dict]) -> bytes:
        """Generate elite consumption report"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=A4, 
            title=self._encode_turkish_text("Elite Tüketim Raporu"),
            topMargin=120,
            bottomMargin=80
        )
        
        story = []
        story.append(Paragraph(self._encode_turkish_text("ELİTE TÜKETİM RAPORU"), self.custom_styles['Title']))
        story.append(Spacer(1, 30))
        
        if consumption_data:
            # Enhanced consumption analysis
            total_electricity = sum(c.get('electricity', 0) for c in consumption_data)
            total_water = sum(c.get('water', 0) for c in consumption_data)
            total_gas = sum(c.get('gas', 0) for c in consumption_data)
            avg_accommodation = sum(c.get('accommodation_count', 0) for c in consumption_data) / len(consumption_data)
            
            # Summary analysis
            summary_data = [
                [self._encode_turkish_text("Metrik"), self._encode_turkish_text("Toplam"), self._encode_turkish_text("Ortalama"), self._encode_turkish_text("Birim")],
                [self._encode_turkish_text("Elektrik Tüketimi"), f"{total_electricity:,.0f}", f"{total_electricity/len(consumption_data):,.0f}", "kWh"],
                [self._encode_turkish_text("Su Tüketimi"), f"{total_water:,.0f}", f"{total_water/len(consumption_data):,.0f}", "m³"],
                [self._encode_turkish_text("Gaz Tüketimi"), f"{total_gas:,.0f}", f"{total_gas/len(consumption_data):,.0f}", "m³"],
                [self._encode_turkish_text("Konaklama"), f"{avg_accommodation:.0f}", f"{avg_accommodation:.0f}", "ort."]
            ]
            
            summary_table = Table(summary_data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 1*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), self.brand_colors['accent']),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), self.bold_font),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
                ('TOPPADDING', (0, 0), (-1, -1), 15),
                ('BACKGROUND', (0, 1), (-1, -1), self.brand_colors['light']),
                ('GRID', (0, 0), (-1, -1), 1, self.brand_colors['border']),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
            ]))
            
            story.append(summary_table)
            story.append(Spacer(1, 30))
            
            # Monthly breakdown
            story.append(Paragraph(self._encode_turkish_text("AYLIK DETAY ANALİZİ"), self.custom_styles['Header']))
            
            consumption_table_data = [[
                self._encode_turkish_text('Ay'), 
                self._encode_turkish_text('Elektrik (kWh)'), 
                self._encode_turkish_text('Su (m³)'), 
                self._encode_turkish_text('Gaz (m³)'), 
                self._encode_turkish_text('Konaklama'),
                self._encode_turkish_text('Verimlilik')
            ]]
            
            for consumption in consumption_data:
                month = self._encode_turkish_text(consumption.get('month', 'Bilinmeyen'))
                electricity = consumption.get('electricity', 0)
                water = consumption.get('water', 0)
                gas = consumption.get('gas', 0)
                accommodation = consumption.get('accommodation_count', 0)
                
                # Calculate efficiency (energy per accommodation)
                efficiency = (electricity / max(1, accommodation)) if accommodation > 0 else 0
                efficiency_status = "🟢" if efficiency < 100 else "🟡" if efficiency < 200 else "🔴"
                
                consumption_table_data.append([
                    month,
                    f"{electricity:,.0f}",
                    f"{water:,.0f}",
                    f"{gas:,.0f}",
                    str(accommodation),
                    efficiency_status
                ])
            
            consumption_table = Table(consumption_table_data, colWidths=[1.2*inch, 1.2*inch, 1.2*inch, 1.2*inch, 1*inch, 1.2*inch])
            consumption_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), self.brand_colors['success']),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), self.bold_font),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('TOPPADDING', (0, 0), (-1, -1), 12),
                ('BACKGROUND', (0, 1), (-1, -1), self.brand_colors['light']),
                ('GRID', (0, 0), (-1, -1), 1, self.brand_colors['border']),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
            ]))
            
            story.append(consumption_table)
        else:
            story.append(Paragraph(
                self._encode_turkish_text("Henüz tüketim verisi bulunmamaktadır. Elite tüketim izleme sistemi kurulması önerilmektedir."), 
                self.custom_styles['Body']
            ))
        
        doc.build(story, onFirstPage=self._add_elite_header_footer, onLaterPages=self._add_elite_header_footer)
        
        buffer.seek(0)
        return buffer.getvalue()


# Global instance
elite_pdf_service = ElitePDFReportService()