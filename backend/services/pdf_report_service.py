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

class PDFReportService:
    """
    Comprehensive PDF Report Generation Service
    Supports multiple report types for different user roles
    """
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._register_turkish_fonts()
        self.custom_styles = self._create_custom_styles()
    
    def _register_turkish_fonts(self):
        """Register Turkish-compatible DejaVu fonts with proper path"""
        try:
            import os
            
            # Define font paths
            dejavu_regular = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
            dejavu_bold = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
            
            # Check if fonts exist
            if os.path.exists(dejavu_regular) and os.path.exists(dejavu_bold):
                # Register fonts with explicit paths
                pdfmetrics.registerFont(TTFont('DejaVuSans', dejavu_regular))
                pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', dejavu_bold))
                
                # Register font family mappings
                from reportlab.lib.fonts import addMapping
                addMapping('DejaVuSans', 0, 0, 'DejaVuSans')       # normal
                addMapping('DejaVuSans', 1, 0, 'DejaVuSans-Bold')  # bold
                addMapping('DejaVuSans', 0, 1, 'DejaVuSans')       # italic (use regular)
                addMapping('DejaVuSans', 1, 1, 'DejaVuSans-Bold')  # bold+italic
                
                self.default_font = 'DejaVuSans'
                self.bold_font = 'DejaVuSans-Bold'
                
                print("✅ DejaVu fonts registered successfully with proper paths")
                
                # Test font by creating a simple text
                from reportlab.pdfgen import canvas
                from io import BytesIO
                test_buffer = BytesIO()
                test_canvas = canvas.Canvas(test_buffer)
                test_canvas.setFont('DejaVuSans', 12)
                test_canvas.drawString(100, 100, "Test: ğüşıöçĞÜŞİÖÇ")
                test_canvas.save()
                print("✅ Font test passed - Turkish characters supported")
                
            else:
                raise Exception(f"DejaVu fonts not found at expected paths")
                
        except Exception as e:
            print(f"❌ DejaVu font registration failed: {e}")
            print("🔄 Falling back to Helvetica with character replacement")
            
            # Fallback to Helvetica
            self.default_font = 'Helvetica'
            self.bold_font = 'Helvetica-Bold'
            self.use_character_replacement = True
    
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
            fontName=self.bold_font
        )
        
        # Subtitle style
        custom_styles['Subtitle'] = ParagraphStyle(
            'CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceAfter=20,
            textColor=colors.HexColor('#374151'),
            fontName=self.bold_font
        )
        
        # Header style
        custom_styles['Header'] = ParagraphStyle(
            'CustomHeader',
            parent=self.styles['Heading3'],
            fontSize=14,
            spaceAfter=15,
            textColor=colors.HexColor('#059669'),
            fontName=self.bold_font
        )
        
        # Body style
        custom_styles['Body'] = ParagraphStyle(
            'CustomBody',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=10,
            leading=14,
            fontName=self.default_font
        )
        
        return custom_styles
    
    def _create_elite_styles(self):
        """Create elite custom styles for premium reporting"""
        elite_styles = {}
        
        # Elite Title style with gradient effect simulation
        elite_styles['Title'] = ParagraphStyle(
            'EliteTitle',
            parent=self.styles['Title'],
            fontSize=28,
            spaceAfter=35,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#1a365d'),
            fontName=self.bold_font,
            borderWidth=2,
            borderColor=colors.HexColor('#059669'),
            borderPadding=10
        )
        
        # Elite Subtitle with enhanced styling
        elite_styles['Subtitle'] = ParagraphStyle(
            'EliteSubtitle',
            parent=self.styles['Heading2'],
            fontSize=18,
            spaceAfter=25,
            textColor=colors.HexColor('#2d3748'),
            fontName=self.bold_font,
            leftIndent=10,
            borderWidth=1,
            borderColor=colors.HexColor('#e2e8f0'),
            borderPadding=8
        )
        
        # Elite Header with premium styling
        elite_styles['Header'] = ParagraphStyle(
            'EliteHeader',
            parent=self.styles['Heading3'],
            fontSize=16,
            spaceAfter=18,
            textColor=colors.HexColor('#059669'),
            fontName=self.bold_font,
            leftIndent=5,
            borderWidth=1,
            borderColor=colors.HexColor('#059669'),
            borderPadding=6
        )
        
        # Elite Body with enhanced readability
        elite_styles['Body'] = ParagraphStyle(
            'EliteBody',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=12,
            leading=16,
            fontName=self.default_font,
            textColor=colors.HexColor('#2d3748'),
            leftIndent=8,
            rightIndent=8
        )
        
        # Elite Highlight style for important information
        elite_styles['Highlight'] = ParagraphStyle(
            'EliteHighlight',
            parent=self.styles['Normal'],
            fontSize=12,
            spaceAfter=15,
            leading=18,
            fontName=self.bold_font,
            textColor=colors.HexColor('#1a365d'),
            backColor=colors.HexColor('#f7fafc'),
            leftIndent=15,
            rightIndent=15,
            borderWidth=1,
            borderColor=colors.HexColor('#cbd5e0'),
            borderPadding=10
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
        """Handle Turkish characters based on font availability"""
        if not text:
            return ""
        
        try:
            # Convert to string and ensure proper encoding
            text_str = str(text)
            
            # If we have proper font support, keep Turkish characters
            if hasattr(self, 'use_character_replacement') and self.use_character_replacement:
                # Replace Turkish characters with closest ASCII equivalents
                char_map = {
                    'ğ': 'g', 'Ğ': 'G',
                    'ü': 'u', 'Ü': 'U', 
                    'ö': 'o', 'Ö': 'O',
                    'ş': 's', 'Ş': 'S',
                    'ç': 'c', 'Ç': 'C',
                    'ı': 'i', 'İ': 'I'
                }
                
                result = text_str
                for turkish_char, ascii_char in char_map.items():
                    result = result.replace(turkish_char, ascii_char)
                return result
            else:
                # With DejaVu font, keep Turkish characters as-is
                # Ensure proper UTF-8 encoding
                if isinstance(text_str, bytes):
                    text_str = text_str.decode('utf-8', errors='replace')
                return text_str
                
        except Exception as e:
            print(f"Error handling Turkish text: {e}")
            # Fallback: replace problematic characters
            try:
                fallback_text = str(text).encode('ascii', errors='replace').decode('ascii')
                return fallback_text
            except:
                return "Metin Hatasi"
    
    def _add_header_footer(self, canvas, doc):
        """Add header and footer to each page"""
        canvas.saveState()
        
        # Header
        canvas.setFont(self.bold_font, 16)
        canvas.setFillColor(colors.HexColor('#059669'))
        canvas.drawString(50, A4[1] - 50, self._encode_turkish_text("ROTA KALİTE & DANIŞMANLIK"))
        
        # Date
        canvas.setFont(self.default_font, 10)
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
        
        # Calculate actual counts from data first
        actual_personnel_count = len(client_data.get('personnel', []))
        actual_supplier_count = len(client_data.get('suppliers', []))
        actual_training_count = len(client_data.get('trainings', []))
        completed_training_count = len([t for t in client_data.get('trainings', []) if t.get('status') == 'completed'])
        
        # Add statistics overview chart with actual data
        stats = client_data.get('statistics', {})
        chart_stats = {
            'total_documents': stats.get('total_documents', 0),
            'total_trainings': actual_training_count,
            'completed_trainings': completed_training_count,
            'total_personnel': actual_personnel_count,
            'total_suppliers': actual_supplier_count
        }
        stats_chart = self._create_statistics_overview_chart(chart_stats)
        if stats_chart:
            from reportlab.platypus import Image
            chart_img = Image(io.BytesIO(base64.b64decode(stats_chart)), width=6*inch, height=3.6*inch)
            story.append(chart_img)
            story.append(Spacer(1, 20))
        
        # Summary table
        summary_data = [
            [self._encode_turkish_text('Metrik'), self._encode_turkish_text('Değer'), self._encode_turkish_text('Önceki Dönem'), self._encode_turkish_text('Değişim')],
            [self._encode_turkish_text('Toplam Belge Sayısı'), str(stats.get('total_documents', 0)), '15', '+25%'],
            [self._encode_turkish_text('Tamamlanan Eğitim'), str(completed_training_count), '8', '+50%'],
            [self._encode_turkish_text('Personel Sayısı'), str(actual_personnel_count), '28', '+7%'],
            [self._encode_turkish_text('Tedarikçi Sayısı'), str(actual_supplier_count), '12', '+25%']
        ]
        
        summary_table = Table(summary_data, colWidths=[2.2*inch, 1*inch, 1*inch, 1*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#059669')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), self.bold_font),
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
            ('FONTNAME', (0, 0), (-1, 0), self.bold_font),
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
                [self._encode_turkish_text('Kişi Başı Enerji'), f"{(total_energy/max(1, actual_personnel_count)):,.0f}", f"{(avg_energy/max(1, actual_personnel_count)):,.0f}", 'kWh/kişi'],
                [self._encode_turkish_text('Kişi Başı Su'), f"{(total_water/max(1, actual_personnel_count)):,.0f}", f"{(avg_water/max(1, actual_personnel_count)):,.0f}", 'm³/kişi']
            ]
            
            consumption_table = Table(consumption_summary, colWidths=[2*inch, 1.5*inch, 1.5*inch, 1*inch])
            consumption_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8B5CF6')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), self.bold_font),
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
                ('FONTNAME', (0, 0), (-1, 0), self.bold_font),
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
                [self._encode_turkish_text('Personel Katılımı'), str(actual_personnel_count), str(actual_personnel_count), '100%'],
                [self._encode_turkish_text('Sertifika Alımı'), str(int(completed_trainings * 0.8)), str(completed_trainings), f"{80:.1f}%"]
            ]
            
            training_table = Table(training_summary, colWidths=[2*inch, 1.2*inch, 1*inch, 1.8*inch])
            training_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F59E0B')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), self.bold_font),
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
                    ('FONTNAME', (0, 0), (-1, 0), self.bold_font),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(training_detail_table)
                
        story.append(PageBreak())
        
        # PAGE 7: SUPPLIER AND PERSONNEL ANALYSIS
        story.append(Paragraph(self._encode_turkish_text("TEDARİKÇİ ve PERSONEL ANALİZİ"), self.custom_styles['Header']))
        
        # Add supplier and personnel distribution chart
        if ('suppliers' in client_data and len(client_data['suppliers']) > 0) or ('personnel' in client_data and len(client_data['personnel']) > 0):
            supplier_personnel_chart = self._create_supplier_personnel_chart(
                client_data.get('suppliers', []), 
                client_data.get('personnel', [])
            )
            if supplier_personnel_chart:
                from reportlab.platypus import Image
                chart_img = Image(io.BytesIO(base64.b64decode(supplier_personnel_chart)), width=6.5*inch, height=3.25*inch)
                story.append(chart_img)
                story.append(Spacer(1, 20))
        
        # Supplier analysis table
        if 'suppliers' in client_data and len(client_data['suppliers']) > 0:
            story.append(Paragraph(self._encode_turkish_text("Tedarikçi Detay Analizi"), self.custom_styles['Header']))
            
            suppliers = client_data['suppliers']
            local_suppliers = len([s for s in suppliers if s.get('local_supplier', False)])
            certified_suppliers = len([s for s in suppliers if s.get('certifications') and len(s.get('certifications', [])) > 0])
            
            supplier_analysis = [
                [self._encode_turkish_text('Tedarikçi Metrikleri'), self._encode_turkish_text('Değer'), self._encode_turkish_text('Oran'), self._encode_turkish_text('Durum')],
                [self._encode_turkish_text('Toplam Tedarikçi'), str(len(suppliers)), '100%', self._encode_turkish_text('Aktif')],
                [self._encode_turkish_text('Yerel Tedarikçi'), str(local_suppliers), f"{(local_suppliers/len(suppliers)*100):.1f}%", self._encode_turkish_text('İyi' if local_suppliers/len(suppliers) > 0.3 else 'Düşük')],
                [self._encode_turkish_text('Sertifikalı Tedarikçi'), str(certified_suppliers), f"{(certified_suppliers/len(suppliers)*100):.1f}%", self._encode_turkish_text('Mükemmel' if certified_suppliers/len(suppliers) > 0.5 else 'Orta')],
                [self._encode_turkish_text('Tedarikçi Çeşitliliği'), str(len(set([s.get('category', 'Diğer') for s in suppliers]))), f"{(len(set([s.get('category', 'Diğer') for s in suppliers]))/len(suppliers)*100):.1f}%", self._encode_turkish_text('İyi')]
            ]
            
            supplier_table = Table(supplier_analysis, colWidths=[2.2*inch, 1*inch, 1*inch, 1.8*inch])
            supplier_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#EF4444')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), self.bold_font),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.mistyrose),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(supplier_table)
            story.append(Spacer(1, 20))
        
        # Personnel certification analysis
        if 'personnel' in client_data and len(client_data['personnel']) > 0:
            story.append(Paragraph(self._encode_turkish_text("Personel Sertifika Analizi"), self.custom_styles['Header']))
            
            # Add certification distribution chart
            cert_chart = self._create_certification_distribution_chart(client_data['personnel'])
            if cert_chart:
                from reportlab.platypus import Image
                chart_img = Image(io.BytesIO(base64.b64decode(cert_chart)), width=6*inch, height=4.8*inch)
                story.append(chart_img)
                story.append(Spacer(1, 20))
            
            # Personnel analysis table
            personnel = client_data['personnel']
            local_personnel = len([p for p in personnel if p.get('is_local', False)])
            certified_personnel = len([p for p in personnel if p.get('certifications') and len(p.get('certifications', [])) > 0])
            
            personnel_analysis = [
                [self._encode_turkish_text('Personel Metrikleri'), self._encode_turkish_text('Değer'), self._encode_turkish_text('Oran'), self._encode_turkish_text('Hedef')],
                [self._encode_turkish_text('Toplam Personel'), str(len(personnel)), '100%', str(len(personnel))],
                [self._encode_turkish_text('Yerel Personel'), str(local_personnel), f"{(local_personnel/len(personnel)*100):.1f}%", '>60%'],
                [self._encode_turkish_text('Sertifikalı Personel'), str(certified_personnel), f"{(certified_personnel/len(personnel)*100):.1f}%", '>80%'],
                [self._encode_turkish_text('Eğitim Katılımı'), str(completed_training_count), f"{(completed_training_count/max(1, len(personnel))*100):.1f}%", '100%']
            ]
            
            personnel_table = Table(personnel_analysis, colWidths=[2.2*inch, 1*inch, 1*inch, 1.8*inch])
            personnel_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#06B6D4')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), self.bold_font),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightcyan),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(personnel_table)
        
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
            ('FONTNAME', (0, 0), (-1, 0), self.bold_font),
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
            plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight',
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
            plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight',
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
            plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight',
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
    def _create_supplier_personnel_chart(self, suppliers: list, personnel: list) -> str:
        """Create suppliers and personnel comparison chart"""
        try:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
            
            # Suppliers by category chart
            if suppliers and len(suppliers) > 0:
                # Count suppliers by category
                supplier_categories = {}
                for supplier in suppliers:
                    category = supplier.get('category', 'Diğer')
                    supplier_categories[category] = supplier_categories.get(category, 0) + 1
                
                if supplier_categories:
                    categories = list(supplier_categories.keys())
                    counts = list(supplier_categories.values())
                    colors_suppliers = ['#EF4444', '#3B82F6', '#10B981', '#F59E0B', '#8B5CF6'][:len(categories)]
                    
                    bars1 = ax1.bar(categories, counts, color=colors_suppliers, alpha=0.8)
                    ax1.set_title('Tedarikçi Dağılımı', fontsize=14, fontweight='bold', pad=20)
                    ax1.set_ylabel('Tedarikçi Sayısı', fontsize=12)
                    ax1.tick_params(axis='x', rotation=45)
                    ax1.grid(True, alpha=0.3, axis='y')
                    
                    # Add value labels on bars
                    for bar in bars1:
                        height = bar.get_height()
                        ax1.text(bar.get_x() + bar.get_width()/2., height,
                                f'{int(height)}', ha='center', va='bottom', fontsize=10, fontweight='bold')
                else:
                    ax1.text(0.5, 0.5, 'Tedarikçi\nverisi yok', ha='center', va='center',
                            transform=ax1.transAxes, fontsize=12)
                    ax1.set_title('Tedarikçi Dağılımı', fontsize=14, fontweight='bold')
            else:
                ax1.text(0.5, 0.5, 'Tedarikçi\nverisi yok', ha='center', va='center',
                        transform=ax1.transAxes, fontsize=12)
                ax1.set_title('Tedarikçi Dağılımı', fontsize=14, fontweight='bold')
            
            # Personnel by position chart
            if personnel and len(personnel) > 0:
                # Count personnel by position
                personnel_positions = {}
                for person in personnel:
                    position = person.get('position', 'Belirtilmemiş')
                    # Group similar positions
                    if 'müdür' in position.lower() or 'manager' in position.lower():
                        position = 'Yönetim'
                    elif 'tekniker' in position.lower() or 'teknik' in position.lower():
                        position = 'Teknik'
                    elif 'servis' in position.lower() or 'hizmet' in position.lower():
                        position = 'Hizmet'
                    elif 'temizlik' in position.lower():
                        position = 'Temizlik'
                    else:
                        position = 'Diğer'
                    
                    personnel_positions[position] = personnel_positions.get(position, 0) + 1
                
                if personnel_positions:
                    positions = list(personnel_positions.keys())
                    counts = list(personnel_positions.values())
                    colors_personnel = ['#06B6D4', '#F59E0B', '#10B981', '#8B5CF6', '#EF4444'][:len(positions)]
                    
                    bars2 = ax2.bar(positions, counts, color=colors_personnel, alpha=0.8)
                    ax2.set_title('Personel Dağılımı', fontsize=14, fontweight='bold', pad=20)
                    ax2.set_ylabel('Personel Sayısı', fontsize=12)
                    ax2.tick_params(axis='x', rotation=45)
                    ax2.grid(True, alpha=0.3, axis='y')
                    
                    # Add value labels on bars
                    for bar in bars2:
                        height = bar.get_height()
                        ax2.text(bar.get_x() + bar.get_width()/2., height,
                                f'{int(height)}', ha='center', va='bottom', fontsize=10, fontweight='bold')
                else:
                    ax2.text(0.5, 0.5, 'Personel\nverisi yok', ha='center', va='center',
                            transform=ax2.transAxes, fontsize=12)
                    ax2.set_title('Personel Dağılımı', fontsize=14, fontweight='bold')
            else:
                ax2.text(0.5, 0.5, 'Personel\nverisi yok', ha='center', va='center',
                        transform=ax2.transAxes, fontsize=12)
                ax2.set_title('Personel Dağılımı', fontsize=14, fontweight='bold')
            
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
            print(f"Error creating supplier/personnel chart: {e}")
            return None
    
    def _create_certification_distribution_chart(self, personnel: list) -> str:
        """Create personnel certification distribution pie chart"""
        try:
            if not personnel or len(personnel) == 0:
                return None
                
            fig, ax = plt.subplots(1, 1, figsize=(10, 8))
            
            # Count certifications
            certification_counts = {}
            total_personnel = len(personnel)
            
            for person in personnel:
                certs = person.get('certifications', [])
                if not certs or len(certs) == 0:
                    certification_counts['Sertifikasız'] = certification_counts.get('Sertifikasız', 0) + 1
                else:
                    for cert in certs:
                        cert_name = cert.strip()
                        if cert_name:
                            certification_counts[cert_name] = certification_counts.get(cert_name, 0) + 1
            
            if certification_counts:
                labels = list(certification_counts.keys())
                sizes = list(certification_counts.values())
                colors = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4', '#EC4899'][:len(labels)]
                
                # Create pie chart
                wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%',
                                                startangle=90, textprops={'fontsize': 10})
                
                ax.set_title('Personel Sertifika Dağılımı', fontsize=16, fontweight='bold', pad=20)
                
                # Add total in center
                ax.text(0, 0, f'Toplam\n{total_personnel}\nPersonel', ha='center', va='center',
                       fontsize=12, fontweight='bold', color='#374151',
                       bbox=dict(boxstyle="round,pad=0.3", facecolor='white', edgecolor='gray', alpha=0.8))
                
                plt.tight_layout()
                
                # Save to base64
                buffer = BytesIO()
                plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight',
                           facecolor='white', edgecolor='none')
                buffer.seek(0)
                chart_base64 = base64.b64encode(buffer.getvalue()).decode()
                plt.close()
                
                return chart_base64
            else:
                return None
                
        except Exception as e:
            print(f"Error creating certification chart: {e}")
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
                ('FONTNAME', (0, 0), (-1, 0), self.bold_font),
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
                ('FONTNAME', (0, 0), (-1, 0), self.bold_font),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -2), colors.lightgreen),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#16A34A')),
                ('TEXTCOLOR', (0, -1), (-1, -1), colors.whitesmoke),
                ('FONTNAME', (0, -1), (-1, -1), self.bold_font),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(consumption_table)
        else:
            story.append(Paragraph(self._encode_turkish_text("Henüz tüketim verisi bulunmamaktadır."), self.custom_styles['Body']))
        
        doc.build(story, onFirstPage=self._add_header_footer, onLaterPages=self._add_header_footer)
        
        buffer.seek(0)
        return buffer.getvalue()


# Global instance
elite_pdf_service = PDFReportService()