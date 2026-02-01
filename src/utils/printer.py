import os

from escpos.printer import Usb, Network
from src.core.localization import lang_manager

class ReceiptPrinter:
    def __init__(self, mode="usb", **kwargs):
        self.mode = mode
        self.kwargs = kwargs
        self.printer = None

    def connect(self):
        try:
            if self.mode == "usb":
                # Typical USB printer IDs, would need configuration
                self.printer = Usb(self.kwargs.get('idVendor', 0x04b8), 
                                 self.kwargs.get('idProduct', 0x0202))
            elif self.mode == "network":
                self.printer = Network(self.kwargs.get('host'))
            return True
        except Exception as e:
            print(f"Printer connection error: {e}")
            return False

    def print_sale_receipt(self, mall, items, gross, discount, net, invoice_num, customer_name=None):
        if not self.printer:
            return False
            
        WIDTH = 32 # standard thermal width
        
        def center(text):
            return text.center(WIDTH)
            
        def hr():
            return "-" * WIDTH

        try:
            qr_path = os.path.join("credentials", "company_qr.png")
            if os.path.exists(qr_path):
                self.printer.image(qr_path)
                self.printer.text("\n")

            # 2. Header
            self.printer.set(align='center', bold=True)
            self.printer.text(center("SALES INVOICE") + "\n")
            self.printer.text(center(f"INVOICE # {invoice_num}") + "\n")
            self.printer.text(hr() + "\n")
            
            # 3. Mall Info
            self.printer.set(align='center', bold=False)
            self.printer.text(center(mall.get("name", "Shop")) + "\n")
            self.printer.text(center(mall.get("address", "")) + "\n")
            self.printer.text(center(f"Phone: {mall.get('phone', '')}") + "\n")
            if mall.get('email'):
                self.printer.text(center(f"Email: {mall.get('email')}") + "\n")
            
            self.printer.text(hr() + "\n")
            
            if customer_name:
                self.printer.set(align='left')
                self.printer.text(f"Customer: {customer_name}\n")
                self.printer.text(hr() + "\n")

            # 4. Table Header
            self.printer.set(align='left', bold=True)
            self.printer.text("Product             Qty   Total\n")
            self.printer.text(hr() + "\n")
            
            # 5. Items
            self.printer.set(bold=False)
            for item in items:
                name = item['name'][:18]
                line = f"{name:<18} {item['qty']:>4} {item['total']:>8.2f}\n"
                self.printer.text(line)
                
            self.printer.text(hr() + "\n")
            
            # 6. Totals
            self.printer.set(align='right', bold=True)
            self.printer.text(f"Gross: {gross:>20.2f}\n")
            self.printer.text(f"Discount: {discount:>17.2f}\n")
            self.printer.text(f"NET: {net:>22.2f} AFN\n")
            
            self.printer.text(hr() + "\n")
            
            # 7. Footer
            self.printer.set(align='center', bold=False)
            self.printer.text(center("Have a Nice Time") + "\n")
            self.printer.text(center("Thanks for Your Visit") + "\n")
            
            self.printer.cut()
            return True
        except Exception as e:
            print(f"Printing error: {e}")
            return False
