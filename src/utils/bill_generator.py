"""
Bill Generator - Creates and prints bills for sales and credits
"""

import os
import tempfile
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from src.database.db_manager import db_manager
from src.core.auth import Auth
from src.core.pharmacy_auth import PharmacyAuth

class BillGenerator:
    """Generates professional bills and receipts"""

    def __init__(self):
        self.company_info = self.load_company_info()
        self.styles = self.setup_styles()

    def load_company_info(self):
        """Load company information from settings"""
        try:
            with db_manager.get_connection() as conn:
                settings = {}
                # Try app_settings first (where we save during onboarding)
                try:
                    rows = conn.execute("SELECT key, value FROM app_settings").fetchall()
                    for row in rows:
                        settings[row['key']] = row['value']
                except: pass
                
                # Fallback to system_settings
                try:
                    rows = conn.execute("SELECT key, value FROM system_settings").fetchall()
                    for row in rows:
                        if row['key'] not in settings:
                            settings[row['key']] = row['value']
                except: pass

                return {
                    'name': settings.get('company_name', 'Your Company Name'),
                    'address': settings.get('company_address', settings.get('address', 'Company Address')),
                    'phone': settings.get('company_phone', settings.get('phone', 'Phone: +1234567890')),
                    'email': settings.get('company_email', settings.get('email', 'Email: info@company.com')),
                    'logo_path': settings.get('company_logo', None)
                }
        except Exception as e:
            print(f"Error loading company info for bill: {e}")
            return {
                'name': 'POS System',
                'address': 'Default Address',
                'phone': 'Phone: 000-000-0000',
                'email': 'Email: info@pos.com',
                'logo_path': None
            }

    def setup_styles(self):
        """Setup PDF styles"""
        styles = getSampleStyleSheet()

        # Custom styles
        styles.add(ParagraphStyle(
            name='CompanyName',
            fontSize=20,
            fontName='Helvetica-Bold',
            alignment=1,  # Center
            spaceAfter=10
        ))

        styles.add(ParagraphStyle(
            name='BillTitle',
            fontSize=16,
            fontName='Helvetica-Bold',
            alignment=1,
            spaceAfter=15
        ))

        styles.add(ParagraphStyle(
            name='NormalCenter',
            fontSize=10,
            alignment=1
        ))

        return styles

    def generate_sales_bill(self, sale_id, is_credit=False, is_pharmacy=False):
        """Generate a sales bill"""
        try:
            db_func = db_manager.get_pharmacy_connection if is_pharmacy else db_manager.get_connection
            with db_func() as conn:
                if is_pharmacy:
                    # Get pharmacy sale details
                    sale = conn.execute("""
                        SELECT s.*, c.name as customer_name, s.total_amount as total_amount
                        FROM pharmacy_sales s
                        LEFT JOIN pharmacy_customers c ON s.customer_id = c.id
                        WHERE s.id = ?
                    """, (sale_id,)).fetchone()
                    
                    items = conn.execute("""
                        SELECT si.*, p.name_en as product_name
                        FROM pharmacy_sale_items si
                        JOIN pharmacy_products p ON si.product_id = p.id
                        WHERE si.sale_id = ?
                    """, (sale_id,)).fetchall()
                else:
                    # Get store sale details
                    sale = conn.execute("""
                        SELECT s.*, c.name_en as customer_name
                        FROM sales s
                        LEFT JOIN customers c ON s.customer_id = c.id
                        WHERE s.id = ?
                    """, (sale_id,)).fetchone()

                    # Get sale items
                    items = conn.execute("""
                        SELECT si.*, p.name_en as product_name
                        FROM sale_items si
                        JOIN products p ON si.product_id = p.id
                        WHERE si.sale_id = ?
                    """, (sale_id,)).fetchall()

                if not sale:
                    raise ValueError("Sale not found")

            return self.create_bill_pdf(sale, items, is_credit, "SALES RECEIPT")

        except Exception as e:
            raise Exception(f"Failed to generate sales bill: {str(e)}")

    def generate_credit_bill(self, loan_id):
        """Generate a credit/loan bill (Currently Pharmacy only as per current logic)"""
        try:
            with db_manager.get_pharmacy_connection() as conn:
                # Get loan details
                loan = conn.execute("""
                    SELECT l.*, c.name as customer_name, s.invoice_number
                    FROM pharmacy_loans l
                    JOIN pharmacy_customers c ON l.customer_id = c.id
                    JOIN pharmacy_sales s ON l.sale_id = s.id
                    WHERE l.id = ?
                """, (loan_id,)).fetchone()

                if not loan:
                    raise ValueError("Loan not found")

                # Get sale items
                items = conn.execute("""
                    SELECT si.*, p.name_en as product_name
                    FROM pharmacy_sale_items si
                    JOIN pharmacy_products p ON si.product_id = p.id
                    WHERE si.sale_id = ?
                """, (loan['sale_id'],)).fetchall()

            return self.create_bill_pdf(loan, items, True, "CREDIT SALES RECEIPT", is_loan=True)

        except Exception as e:
            raise Exception(f"Failed to generate credit bill: {str(e)}")

    def create_bill_pdf(self, transaction, items, is_credit, title, is_loan=False):
        """Create the actual PDF bill"""
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_file.close()

        doc = SimpleDocTemplate(temp_file.name, pagesize=A4)
        elements = []

        # Company Header
        if self.company_info['logo_path'] and os.path.exists(self.company_info['logo_path']):
            logo = Image(self.company_info['logo_path'], 2*inch, 1*inch)
            elements.append(logo)
            elements.append(Spacer(1, 12))

        elements.append(Paragraph(self.company_info['name'], self.styles['CompanyName']))
        elements.append(Paragraph(self.company_info['address'], self.styles['NormalCenter']))
        elements.append(Paragraph(self.company_info['phone'], self.styles['NormalCenter']))
        elements.append(Paragraph(self.company_info['email'], self.styles['NormalCenter']))
        elements.append(Spacer(1, 20))

        # Bill Title
        elements.append(Paragraph(title, self.styles['BillTitle']))

        # Bill Info
        bill_info = [
            ["Bill No:", transaction.get('invoice_number', f"#{transaction['id']}")],
            ["Date:", transaction['created_at'][:10] if isinstance(transaction['created_at'], str) else transaction['created_at'].strftime('%Y-%m-%d')],
            ["Time:", transaction['created_at'][11:19] if isinstance(transaction['created_at'], str) else transaction['created_at'].strftime('%H:%M:%S')],
        ]

        if 'customer_name' in transaction and transaction['customer_name']:
            bill_info.append(["Customer:", transaction['customer_name']])

        if is_credit:
            bill_info.append(["Payment Type:", "CREDIT/LOAN"])
        else:
            bill_info.append(["Payment Type:", transaction.get('payment_type', 'CASH')])

        bill_table = Table(bill_info, colWidths=[80, 200])
        bill_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))
        elements.append(bill_table)
        elements.append(Spacer(1, 20))

        # Items Table
        table_data = [['Item', 'Qty', 'Price', 'Total']]
        total_amount = 0

        for item in items:
            qty = item['quantity']
            price = item['unit_price'] if 'unit_price' in item else item['sale_price']
            total = qty * price
            total_amount += total

            table_data.append([
                item.get('product_name', 'Unknown Product'),
                str(qty),
                f"{price:.2f}",
                f"{total:.2f}"
            ])

        # Add totals
        table_data.append(['', '', 'TOTAL:', f"{total_amount:.2f}"])

        if is_credit and 'total_amount' in transaction:
            table_data.append(['', '', 'PAID:', f"{transaction['total_amount'] - transaction.get('balance', 0):.2f}"])
            table_data.append(['', '', 'BALANCE:', f"{transaction.get('balance', 0):.2f}"])

        items_table = Table(table_data, colWidths=[200, 50, 70, 70])
        items_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (3, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
        ]))
        elements.append(items_table)
        elements.append(Spacer(1, 30))

        # Footer
        elements.append(Paragraph("Thank you for your business!", self.styles['NormalCenter']))
        elements.append(Paragraph("Please keep this receipt for your records.", self.styles['NormalCenter']))

        # Build PDF
        doc.build(elements)

        return temp_file.name

    def print_bill(self, pdf_path):
        """Print the generated bill"""
        try:
            import subprocess
            import platform

            if platform.system() == "Darwin":  # macOS
                subprocess.run(['open', pdf_path])
            elif platform.system() == "Windows":
                os.startfile(pdf_path)
            else:  # Linux
                subprocess.run(['xdg-open', pdf_path])

            return True
        except Exception as e:
            raise Exception(f"Failed to print bill: {str(e)}")

# Global instance
bill_generator = BillGenerator()