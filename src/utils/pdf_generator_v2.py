import os
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from src.database.db_manager import db_manager

class PDFReportGeneratorV2:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        self.styles.add(ParagraphStyle(
            name='CenteredTitle',
            parent=self.styles['Heading1'],
            alignment=TA_CENTER,
            spaceAfter=12
        ))
        self.styles.add(ParagraphStyle(
            name='RightAligned',
            parent=self.styles['Normal'],
            alignment=TA_RIGHT
        ))
        self.styles.add(ParagraphStyle(
            name='CompanyHeader',
            fontSize=18,
            fontName='Helvetica-Bold',
            alignment=TA_CENTER,
            spaceAfter=6
        ))
        self.styles.add(ParagraphStyle(
            name='CompanySubHeader',
            fontSize=10,
            fontName='Helvetica',
            alignment=TA_CENTER,
            spaceAfter=12
        ))

    def _get_company_info(self, is_pharmacy=False):
        """Fetch company info from DB"""
        db_func = db_manager.get_pharmacy_connection if is_pharmacy else db_manager.get_connection
        try:
            with db_func() as conn:
                info = {
                    'name': 'Faqiri POS' if not is_pharmacy else 'Faqiri Pharmacy',
                    'address': 'Kabul, Afghanistan',
                    'phone': '0700000000',
                    'email': 'info@mall.af'
                }
                
                table = "pharmacy_info" if is_pharmacy else "company_info"
                cursor = conn.cursor()
                cursor.execute(f"SELECT name, address, phone, email FROM {table} LIMIT 1")
                row = cursor.fetchone()
                if row:
                    info['name'] = row[0] or info['name']
                    info['address'] = row[1] or info['address']
                    info['phone'] = row[2] or info['phone']
                    info['email'] = row[3] or info['email']
                return info
        except:
             return {'name': 'Faqiri POS', 'address': 'Kabul, Afghanistan', 'phone': '0700000000', 'email': 'info@mall.af'}

    def generate_table_report(self, file_path, title, headers, data, landscape_mode=False, is_pharmacy=False):
        """
        Generic table report generator
        headers: List of strings
        data: List of lists (all items converted to string)
        """
        page_size = landscape(A4) if landscape_mode else A4
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        doc = SimpleDocTemplate(file_path, pagesize=page_size)
        elements = []
        
        # 1. Branding Header
        company = self._get_company_info(is_pharmacy)
        elements.append(Paragraph(company['name'], self.styles['CompanyHeader']))
        elements.append(Paragraph(f"{company['address']} | Phone: {company['phone']} | Email: {company['email']}", self.styles['CompanySubHeader']))
        elements.append(Spacer(1, 12))
        
        # 2. Title & Date
        elements.append(Paragraph(title, self.styles['CenteredTitle']))
        elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}", self.styles['RightAligned']))
        elements.append(Spacer(1, 24))
        
        # 3. Table
        if not data:
            elements.append(Paragraph("No records found for the selected criteria.", self.styles['Normal']))
        else:
            # Prepend headers to data
            table_data = [headers] + data
            
            # Calculate col widths (automatic or proportional)
            col_count = len(headers)
            avail_width = page_size[0] - (doc.leftMargin + doc.rightMargin)
            col_widths = [avail_width / col_count] * col_count
            
            t = Table(table_data, colWidths=col_widths, repeatRows=1)
            
            # Style
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#4318ff")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                # zebra striping
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey])
            ]))
            
            elements.append(t)
        
        # Footer
        elements.append(Spacer(1, 48))
        elements.append(Paragraph(f"Page 1 of 1 (V2 Generator)", self.styles['Normal']))
        
        # Build
    def generate_multi_table_report(self, file_path, title, sections, landscape_mode=True, is_pharmacy=False):
        """
        Generate report with multiple tables/sections
        sections: List of dicts: {'title': str, 'headers': list, 'data': list, 'type': 'table'}
        """
        page_size = landscape(A4) if landscape_mode else A4
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        doc = SimpleDocTemplate(file_path, pagesize=page_size)
        elements = []
        
        # Header
        company = self._get_company_info(is_pharmacy)
        elements.append(Paragraph(company['name'], self.styles['CompanyHeader']))
        elements.append(Paragraph(f"{company['address']} | Phone: {company['phone']}", self.styles['CompanySubHeader']))
        elements.append(Spacer(1, 12))
        
        elements.append(Paragraph(title, self.styles['CenteredTitle']))
        elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}", self.styles['RightAligned']))
        elements.append(Spacer(1, 12))

        for section in sections:
            elements.append(Paragraph(f"<b>{section['title']}</b>", self.styles['Heading2']))
            elements.append(Spacer(1, 6))
            
            headers = section['headers']
            data = section['data']
            
            if not data:
                elements.append(Paragraph("No records found.", self.styles['Normal']))
            else:
                table_data = [headers] + data
                col_count = len(headers)
                avail_width = page_size[0] - (doc.leftMargin + doc.rightMargin)
                col_widths = [avail_width / col_count] * col_count
                
                t = Table(table_data, colWidths=col_widths, repeatRows=1)
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#4318ff")),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey])
                ]))
                elements.append(t)
            
            elements.append(Spacer(1, 24))

        doc.build(elements)
        return file_path

pdf_generator_v2 = PDFReportGeneratorV2()
