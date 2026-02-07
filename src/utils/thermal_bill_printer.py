"""
Thermal Bill Printer - Creates formatted thermal-style receipts
Based on demand.txt requirements

UPGRADES (as requested):
1) Auto-print instead of opening text file
2) QR code smaller + centered (does not take all width)
"""

import os
import qrcode
from datetime import datetime
from src.database.db_manager import db_manager
import subprocess
import platform


class ThermalBillPrinter:
    """Generates thermal-style bills matching exact format from demand.txt"""
    
    def __init__(self):
        self.width = 42  # Character width for thermal printer (80mm)
    
    def load_company_info(self, is_pharmacy=False):
        """Load company information from settings"""
        try:
            db_func = db_manager.get_pharmacy_connection if is_pharmacy else db_manager.get_connection
            with db_func() as conn:
                # Default values
                info = {
                    'name': 'Kabul City Center' if not is_pharmacy else 'FaqiriTech Pharmacy',
                    'address': 'Main Road, Kabul, Afghanistan',
                    'phone': '0700000000',
                    'email': 'info@mall.af' if not is_pharmacy else 'pharmacy@FaqiriTech.com'
                }
                
                # Try pharmacy_info/company_info first
                if is_pharmacy:
                    try:
                        cursor = conn.cursor()
                        cursor.execute("SELECT name, address, phone, email FROM pharmacy_info LIMIT 1")
                        row = cursor.fetchone()
                        if row:
                            info['name'] = row['name'] or info['name']
                            info['address'] = row['address'] or info['address']
                            info['phone'] = row['phone'] or info['phone']
                            info['email'] = row['email'] or info['email']
                    except:
                        pass
                else:
                    try:
                        cursor = conn.cursor()
                        cursor.execute("SELECT name, address, phone, email FROM company_info LIMIT 1")
                        row = cursor.fetchone()
                        if row:
                            info['name'] = row['name'] or info['name']
                            info['address'] = row['address'] or info['address']
                            info['phone'] = row['phone'] or info['phone']
                            info['email'] = row['email'] or info['email']
                    except:
                        # Fallback: app_settings
                        try:
                            rows = conn.execute("SELECT key, value FROM app_settings").fetchall()
                            for row in rows:
                                if row['key'] == 'company_name': info['name'] = row['value']
                                if row['key'] == 'company_address': info['address'] = row['value']
                                if row['key'] == 'company_phone': info['phone'] = row['value']
                                if row['key'] == 'company_email': info['email'] = row['value']
                        except:
                            pass

                # Fetch WhatsApp and Receipt Notes (common in app_settings for both)
                try:
                    rows = conn.execute("""
                        SELECT key, value FROM app_settings 
                        WHERE key IN ('whatsapp_number', 'walking_receipt_note', 'loan_receipt_note', 'receipt_note')
                    """).fetchall()
                    for row in rows:
                        if row['key'] == 'whatsapp_number':
                            info['whatsapp'] = row['value']
                        elif row['key'] == 'walking_receipt_note':
                            info['walking_note'] = row['value']
                        elif row['key'] == 'loan_receipt_note':
                            info['loan_note'] = row['value']
                        elif row['key'] == 'receipt_note':
                            info['receipt_note'] = row['value']
                except: pass

                return info
        except Exception as e:
            print(f"Error loading company info for bill: {e}")
            return {
                'name': 'FaqiriTech Business',
                'address': 'Kabul, Afghanistan',
                'phone': '0700000000',
                'email': 'info@afex.com'
            }
    
    def center_text(self, text):
        """Center text based on thermal printer width"""
        if len(text) >= self.width:
            return text[:self.width]
        padding = (self.width - len(text)) // 2
        return ' ' * padding + text
    
    def center_wrapped_text(self, text):
        """Wrap and center text blocks"""
        lines = []
        words = text.split()
        cur = ""
        for w in words:
            if len(cur) + (1 if cur else 0) + len(w) <= self.width:
                cur = f"{cur} {w}".strip()
            else:
                if cur:
                    lines.append(self.center_text(cur))
                cur = w
        if cur:
            lines.append(self.center_text(cur))
        return "\n".join(lines)
    
    def separator(self, char='-'):
        """Create separator line"""
        return char * self.width
    
    def number_to_words_afn(self, amount):
        """Convert number to words (Afghanis)"""
        ones = ['', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine']
        teens = ['Ten', 'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 
                 'Sixteen', 'Seventeen', 'Eighteen', 'Nineteen']
        tens = ['', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety']
        
        def convert_hundreds(n):
            if n == 0: return ''
            elif n < 10: return ones[n]
            elif n < 20: return teens[n - 10]
            elif n < 100: return tens[n // 10] + ('' if n % 10 == 0 else ' ' + ones[n % 10])
            else: return ones[n // 100] + ' Hundred' + ('' if n % 100 == 0 else ' ' + convert_hundreds(n % 100))
        
        num = int(amount)
        if num == 0: return "Zero Afghanis Only"
        
        if num < 1000:
            return f"{convert_hundreds(num)} Afghanis Only"
        elif num < 1000000:
            thousands = num // 1000
            remainder = num % 1000
            result = f"{convert_hundreds(thousands)} Thousand"
            if remainder > 0: result += f" {convert_hundreds(remainder)}"
            return f"{result} Afghanis Only"
        else:
            return f"{num:,.0f} Afghanis Only"

    # ============================================================
    # ✅ FIXED: SMALLER QR (does NOT take full width) + centered
    # ============================================================
    def _downscale_matrix(self, matrix, target_width):
        """
        Downscale QR matrix to fit nicely inside receipt width.
        Uses block sampling: if any cell in block is True => black.
        """
        size = len(matrix)
        if size <= target_width:
            return matrix  # already small enough

        # scale factor (ceil)
        scale = (size + target_width - 1) // target_width
        new = []
        for r in range(0, size, scale):
            new_row = []
            for c in range(0, size, scale):
                block_black = False
                for rr in range(r, min(r + scale, size)):
                    for cc in range(c, min(c + scale, size)):
                        if matrix[rr][cc]:
                            block_black = True
                            break
                    if block_black:
                        break
                new_row.append(block_black)
            new.append(new_row)
        return new

    def generate_qr_code(self, data):
        """Generate compact QR code using half-block characters (Square Aspect Ratio)"""
        try:
            # Low error correction to keep size minimal
            qr = qrcode.QRCode(
                version=1, 
                box_size=1, 
                border=1, 
                error_correction=qrcode.constants.ERROR_CORRECT_L
            )
            qr.add_data(data)
            qr.make(fit=True)
            matrix = qr.get_matrix()
            
            # Text-based QR using half-blocks to fix aspect ratio
            # (Thermal printers often have tall line spacing, making 1 char = 2 vertical pixels helps)
            qr_ascii = ""
            rows = len(matrix)
            cols = len(matrix[0])
            
            for r in range(0, rows, 2):
                line = ""
                for c in range(cols):
                    top = matrix[r][c]
                    # Check bottom pixel (handle odd height)
                    bottom = False
                    if r + 1 < rows:
                        bottom = matrix[r+1][c]
                    
                    if top and bottom:
                        char = "█"
                    elif top and not bottom:
                        char = "▀"
                    elif not top and bottom:
                        char = "▄"
                    else:
                        char = " "
                    line += char
                
                # Left aligned (as requested)
                qr_ascii += line + "\n"
                
            return qr_ascii
        except Exception as e:
            print(f"QR generation error: {e}")
            return "[QR Code]"
    
    def format_product_line(self, s_no, product_name, qty, price, total):
        """Format product line with wrapping for long names"""
        lines = []
        max_name_len = self.width - 22
        if len(product_name) <= max_name_len:
            line = f"{s_no:<3} {product_name:<{max_name_len}} {qty:>2} {price:>7.2f} {total:>7.2f}"
            lines.append(line)
        else:
            first_line = f"{s_no:<3} {product_name[:max_name_len]}"
            lines.append(first_line)
            remaining = product_name[max_name_len:]
            while remaining:
                chunk = remaining[:max_name_len + 4]
                lines.append(f"    {chunk}")
                remaining = remaining[max_name_len + 4:]
            lines.append(f"    {'':<{max_name_len}} {qty:>2} {price:>7.2f} {total:>7.2f}")
        return lines
    
    def generate_sales_bill(self, sale_id, is_credit=False, is_pharmacy=False):
        """Generate thermal-style sales bill"""
        try:
            db_func = db_manager.get_pharmacy_connection if is_pharmacy else db_manager.get_connection
            with db_func() as conn:
                if is_pharmacy:
                    sale = conn.execute("""
                        SELECT s.*, c.name as customer_name
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
                    sale = conn.execute("""
                        SELECT s.*, c.name_en as customer_name
                        FROM sales s
                        LEFT JOIN customers c ON s.customer_id = c.id
                        WHERE s.id = ?
                    """, (sale_id,)).fetchone()
                    items = conn.execute("""
                        SELECT si.*, p.name_en as product_name
                        FROM sale_items si
                        JOIN products p ON si.product_id = p.id
                        WHERE si.sale_id = ?
                    """, (sale_id,)).fetchall()

                if not sale:
                    raise ValueError("Sale not found")

                sale_dict = dict(sale)
                items_list = [dict(item) for item in items]

            return self.create_thermal_bill(sale_dict, items_list, is_credit, is_pharmacy)
        except Exception as e:
            raise Exception(f"Failed to generate sales bill: {str(e)}")
    
    def create_thermal_bill(self, transaction, items, is_credit, is_pharmacy=False):
        """Create thermal-style bill matching demand.txt format"""
        bill_text = ""
        company_info = self.load_company_info(is_pharmacy)
        
        bill_text += self.center_text("SALES INVOICE") + "\n"
        invoice_num = transaction.get('invoice_number', f"#{transaction['id']:04d}")
        bill_text += self.center_text(f"INVOICE # {invoice_num}") + "\n"
        bill_text += self.separator() + "\n"
        bill_text += self.separator("-") + "\n"
        
        bill_text += self.center_wrapped_text(company_info['name']) + "\n"
        bill_text += self.center_wrapped_text(company_info['address']) + "\n"
        bill_text += self.center_text(f"Phone: {company_info['phone']}") + "\n"
        bill_text += self.center_text(f"Email: {company_info['email']}") + "\n"
        bill_text += self.separator() + "\n"
        
        bill_text += f"S#  Product Name           Qty  Price  Total\n"
        bill_text += self.separator() + "\n"
        
        total_amount = 0
        for idx, item in enumerate(items, start=1):
            qty = item['quantity']
            price = item.get('unit_price', item.get('sale_price', 0))
            total = qty * price
            total_amount += total
            product_name = item.get('product_name', 'Unknown Product')
            product_lines = self.format_product_line(idx, product_name, qty, price, total)
            for line in product_lines:
                bill_text += line + "\n"
        
        bill_text += self.separator() + "\n"
        discount = transaction.get('discount', 0)
        gross_amount = total_amount
        net_amount = gross_amount - discount
        
        bill_text += self.center_text(f"NET AMOUNT: {net_amount:.2f} AFN") + "\n"
        bill_text += "Amount in Words:\n"
        bill_text += self.number_to_words_afn(net_amount) + "\n"
        bill_text += self.separator() + "\n"
        
        if discount > 0:
            bill_text += f"Discount:{discount:>30.2f}\n"
        bill_text += f"Gross Amount:{gross_amount:>26.2f}\n"
        bill_text += f"Net Amount:{net_amount:>28.2f}\n"
        bill_text += self.separator() + "\n"
        
        # Shorten date for smaller QR (YYYYMMDD only)
        # QR Code: WhatsApp if available, else Invoice info
        qr_content = f"{invoice_num}|{net_amount:.2f}"
        if company_info.get('whatsapp'):
            # Standard WhatsApp link format
            clean_num = company_info['whatsapp'].replace('+', '').replace(' ', '')
            qr_content = f"https://wa.me/{clean_num}"
        
        bill_text += self.generate_qr_code(qr_content) + "\n"
        
        # Determine which note to use
        custom_note = None
        if is_credit:
            custom_note = company_info.get('loan_note')
        else:
            custom_note = company_info.get('walking_note') or company_info.get('receipt_note')

        # Add Custom Receipt Note if exists
        if custom_note:
            bill_text += self.separator("-") + "\n"
            note = custom_note
            # Simple wrapping
            while len(note) > self.width:
                split_idx = note[:self.width].rfind(' ')
                if split_idx == -1: split_idx = self.width
                bill_text += self.center_text(note[:split_idx].strip()) + "\n"
                note = note[split_idx:].strip()
            bill_text += self.center_text(note) + "\n"
            bill_text += self.separator("-") + "\n"

        # Special msg for credit/loan customers
        if is_credit:
            bill_text += "\n" + self.center_text("!!! PAYMENT REQUEST !!!") + "\n"
            msg = "We request you to pay the outstanding amount soon, as it relates to an employee's salary."
            # Wrap msg
            temp_msg = msg
            while len(temp_msg) > self.width:
                split_idx = temp_msg[:self.width].rfind(' ')
                if split_idx == -1: split_idx = self.width
                bill_text += temp_msg[:split_idx].strip() + "\n"
                temp_msg = temp_msg[split_idx:].strip()
            bill_text += temp_msg + "\n"
            bill_text += f"\nLoan Amount: {net_amount:,.2f} AFN\n"
            bill_text += self.separator("-") + "\n"

        bill_text += self.center_text("Have a Nice Time") + "\n"
        bill_text += self.center_text("Thanks for Your Kind Visit") + "\n"
        bill_text += "\n\n\n\n" # Feed paper before cut
        
        return bill_text

    # ============================================================
    # ✅ AUTO-PRINT: send to default printer (no opening file)
    # ============================================================
    def _send_to_printer(self, filepath):
        system = platform.system()

        # Windows: print using default associated app/printer
        if system == "Windows":
            try:
                # This sends file to default printer silently (depends on system config)
                os.startfile(filepath, "print")
                return
            except Exception as e:
                print(f"Windows print failed: {e}")
                os.startfile(filepath) # Fallback to open
                return

        # macOS / Linux: use lp or lpr
        # Try lp first, then lpr
        try:
            subprocess.run(["lp", filepath], check=True, capture_output=True)
            return
        except Exception:
            pass

        try:
            subprocess.run(["lpr", filepath], check=True, capture_output=True)
            return
        except Exception as e:
            # FALLBACK: If hardware print fails (e.g. no printer), open the file for viewing
            print(f"Direct print failed ({e}), falling back to preview.")
            try:
                if system == "Darwin":
                    subprocess.run(['open', filepath])
                elif system == "Linux":
                    subprocess.run(['xdg-open', filepath])
            except:
                pass # Last resort: do nothing if even open fails

    def print_bill(self, bill_text):
        """Auto-print the bill (still writes a temp file, but prints it immediately)"""
        try:
            bills_dir = os.path.join("data", "receipts")
            os.makedirs(bills_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(bills_dir, f"bill_{timestamp}.txt")

            # Write receipt text
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(bill_text)

            # Auto-print
            self._send_to_printer(filename)

            return filename
        except Exception as e:
            raise Exception(f"Failed to print bill: {str(e)}")


thermal_printer = ThermalBillPrinter()
