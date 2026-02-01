import os
import sys
import platform
import subprocess
import tempfile
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict

# Preview PDF (for testing without printer)
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm


# -----------------------------
# ESC/POS helpers (RAW printing)
# -----------------------------
ESC = b"\x1b"
GS  = b"\x1d"

def esc_init() -> bytes:
    return ESC + b"@"  # Initialize

def esc_align(n: int) -> bytes:
    # 0=left,1=center,2=right
    return ESC + b"a" + bytes([n])

def esc_bold(on: bool) -> bytes:
    return ESC + b"E" + (b"\x01" if on else b"\x00")

def esc_underline(on: bool) -> bytes:
    return ESC + b"-" + (b"\x01" if on else b"\x00")

def esc_font_size(w: int = 1, h: int = 1) -> bytes:
    """
    w,h: 1..8
    ESC ! doesn't control both well across models, GS ! is common:
    GS ! n : bits 0-3 height, 4-7 width
    n = ((w-1)<<4) | (h-1)
    """
    w = max(1, min(8, w))
    h = max(1, min(8, h))
    n = ((w - 1) << 4) | (h - 1)
    return GS + b"!" + bytes([n])

def esc_cut() -> bytes:
    # Partial cut
    return GS + b"V" + b"\x01"

def esc_feed(lines: int = 1) -> bytes:
    return ESC + b"d" + bytes([max(0, min(255, lines))])

def esc_line(text: str = "") -> bytes:
    return text.encode("utf-8", errors="replace") + b"\n"

def esc_hr(width_chars: int) -> bytes:
    return esc_line("-" * width_chars)

def wrap_text(text: str, width: int) -> List[str]:
    words = text.split()
    lines = []
    cur = ""
    for w in words:
        if len(cur) + (1 if cur else 0) + len(w) <= width:
            cur = f"{cur} {w}".strip()
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


# -----------------------------
# Receipt domain models
# -----------------------------
@dataclass
class ReceiptItem:
    name: str
    qty: float
    price: float  # unit price
    sku: str = ""

    @property
    def total(self) -> float:
        return self.qty * self.price

@dataclass
class BrandHeaderFooter:
    brand_name: str
    slogan: str = ""
    address_lines: List[str] = field(default_factory=list)
    phone: str = ""
    website: str = ""
    tax_id: str = ""       # e.g., VAT/TIN
    mall_name: str = ""    # e.g., "Kabul City Center"
    footer_lines: List[str] = field(default_factory=list)
    return_policy: str = "Returns within 7 days with receipt."
    thank_you: str = "Thank you for shopping with us!"
    social: str = ""       # e.g., "@brandname"
    qr_text: str = ""      # printed as text hint (true QR needs image)

@dataclass
class ReceiptOrder:
    invoice_no: str
    datetime_local: datetime
    cashier: str
    customer: str = ""
    items: List[ReceiptItem] = field(default_factory=list)
    discount: float = 0.0
    tax_rate: float = 0.0  # e.g., 0.10 for 10%
    currency: str = "AFN"
    payment_method: str = "Cash"
    amount_paid: float = 0.0

    @property
    def subtotal(self) -> float:
        return sum(i.total for i in self.items)

    @property
    def tax_amount(self) -> float:
        taxable = max(0.0, self.subtotal - self.discount)
        return taxable * self.tax_rate

    @property
    def total(self) -> float:
        return max(0.0, self.subtotal - self.discount) + self.tax_amount

    @property
    def change(self) -> float:
        return max(0.0, self.amount_paid - self.total)


# -----------------------------
# Printer detection & RAW send
# -----------------------------
def list_printers_windows() -> List[str]:
    printers = []
    try:
        import win32print  # type: ignore
        flags = win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
        for p in win32print.EnumPrinters(flags):
            # p[2] is printer name
            printers.append(p[2])
    except Exception:
        # fallback: wmic (older), may fail on some systems
        try:
            out = subprocess.check_output(["wmic", "printer", "get", "name"], stderr=subprocess.STDOUT, text=True)
            lines = [ln.strip() for ln in out.splitlines() if ln.strip() and ln.strip().lower() != "name"]
            printers.extend(lines)
        except Exception:
            pass
    return sorted(set(printers))

def list_printers_unix() -> List[str]:
    printers = []
    # lpstat is common on Linux/macOS if CUPS is present
    try:
        out = subprocess.check_output(["lpstat", "-p"], stderr=subprocess.STDOUT, text=True)
        for ln in out.splitlines():
            ln = ln.strip()
            # "printer PRINTERNAME is idle. enabled since ..."
            if ln.startswith("printer "):
                parts = ln.split()
                if len(parts) >= 2:
                    printers.append(parts[1])
    except Exception:
        pass
    return sorted(set(printers))

def detect_printers() -> List[str]:
    sysname = platform.system().lower()
    if "windows" in sysname:
        return list_printers_windows()
    return list_printers_unix()

THERMAL_KEYWORDS = [
    "thermal", "receipt", "pos", "epson", "bixolon", "star", "tm-t", "tm t", "rp", "xp", "printer"
]

def pick_best_printer(printers: List[str]) -> Optional[str]:
    if not printers:
        return None
    scored: List[Tuple[int, str]] = []
    for p in printers:
        name = p.lower()
        score = 0
        for kw in THERMAL_KEYWORDS:
            if kw in name:
                score += 2
        # prefer shorter "device-like" names a bit
        score += max(0, 10 - len(p) // 6)
        scored.append((score, p))
    scored.sort(reverse=True, key=lambda x: x[0])
    return scored[0][1] if scored else printers[0]

def send_raw_to_printer(printer_name: str, data: bytes) -> None:
    sysname = platform.system().lower()

    if "windows" in sysname:
        # Best: win32print RAW job
        try:
            import win32print  # type: ignore
            h = win32print.OpenPrinter(printer_name)
            try:
                job = win32print.StartDocPrinter(h, 1, ("Receipt", None, "RAW"))
                win32print.StartPagePrinter(h)
                win32print.WritePrinter(h, data)
                win32print.EndPagePrinter(h)
                win32print.EndDocPrinter(h)
            finally:
                win32print.ClosePrinter(h)
            return
        except Exception as e:
            raise RuntimeError(f"Windows RAW print failed for '{printer_name}': {e}")

    # Linux/macOS via CUPS: use lp -o raw
    try:
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(data)
            tmp_path = f.name
        subprocess.check_call(["lp", "-d", printer_name, "-o", "raw", tmp_path])
    except Exception as e:
        raise RuntimeError(f"CUPS RAW print failed for '{printer_name}': {e}")
    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass


# -----------------------------
# Receipt formatting (ESC/POS)
# -----------------------------
def money(x: float) -> str:
    return f"{x:,.2f}"

def format_two_col(left: str, right: str, width: int) -> str:
    # right aligned
    space = max(1, width - len(left) - len(right))
    return left + (" " * space) + right

def build_receipt_escpos(
    order: ReceiptOrder,
    brand: BrandHeaderFooter,
    width_chars: int = 42
) -> bytes:
    b = bytearray()
    b += esc_init()

    # Header (mall/brand)
    b += esc_align(1)
    b += esc_font_size(2, 2)
    b += esc_bold(True)
    for wln in wrap_text(brand.brand_name, width_chars // 2): # //2 because size 2,2 doubles width
        b += esc_line(wln)
    b += esc_bold(False)
    b += esc_font_size(1, 1)

    if brand.slogan:
        for wln in wrap_text(brand.slogan, width_chars):
            b += esc_line(wln)

    if brand.mall_name:
        b += esc_line(brand.mall_name)

    b += esc_align(1)
    for ln in brand.address_lines:
        for wln in wrap_text(ln, width_chars):
            b += esc_line(wln)

    if brand.phone:
        b += esc_line(f"Tel: {brand.phone}")
    if brand.website:
        b += esc_line(brand.website)
    if brand.tax_id:
        b += esc_line(f"Tax ID: {brand.tax_id}")

    b += esc_hr(width_chars)

    # Order meta
    b += esc_align(0)
    dt_str = order.datetime_local.strftime("%Y-%m-%d %H:%M:%S")
    b += esc_line(format_two_col("Invoice:", order.invoice_no, width_chars))
    b += esc_line(format_two_col("Date:", dt_str, width_chars))
    b += esc_line(format_two_col("Cashier:", order.cashier, width_chars))
    if order.customer:
        b += esc_line(format_two_col("Customer:", order.customer, width_chars))

    b += esc_hr(width_chars)

    # Items header
    # Layout: name (wrap) then qty x price and line total
    b += esc_bold(True)
    b += esc_line(format_two_col("Item", "Total", width_chars))
    b += esc_bold(False)
    b += esc_hr(width_chars)

    for it in order.items:
        # Item name lines
        name_lines = wrap_text(it.name, width_chars)
        b += esc_line(name_lines[0])
        for extra in name_lines[1:]:
            b += esc_line(extra)

        # Qty/price line
        left = f"{it.qty:g} x {money(it.price)} {order.currency}"
        right = f"{money(it.total)} {order.currency}"
        b += esc_line(format_two_col(left, right, width_chars))

        if it.sku:
            b += esc_line(f"SKU: {it.sku}")

        b += esc_line("")  # blank line between items

    b += esc_hr(width_chars)

    # Totals
    b += esc_line(format_two_col("Subtotal", f"{money(order.subtotal)} {order.currency}", width_chars))
    if order.discount > 0:
        b += esc_line(format_two_col("Discount", f"-{money(order.discount)} {order.currency}", width_chars))
    if order.tax_rate > 0:
        b += esc_line(format_two_col(f"Tax ({order.tax_rate*100:.0f}%)", f"{money(order.tax_amount)} {order.currency}", width_chars))

    b += esc_bold(True)
    b += esc_font_size(2, 2)
    b += esc_line(format_two_col("TOTAL", f"{money(order.total)} {order.currency}", width_chars))
    b += esc_font_size(1, 1)
    b += esc_bold(False)

    b += esc_hr(width_chars)

    # Payment
    b += esc_line(format_two_col("Payment", order.payment_method, width_chars))
    if order.amount_paid > 0:
        b += esc_line(format_two_col("Paid", f"{money(order.amount_paid)} {order.currency}", width_chars))
        b += esc_line(format_two_col("Change", f"{money(order.change)} {order.currency}", width_chars))

    b += esc_hr(width_chars)

    # Footer (policy + thanks + social + QR text)
    b += esc_align(1)

    if brand.thank_you:
        b += esc_bold(True)
        b += esc_line(brand.thank_you)
        b += esc_bold(False)

    if brand.return_policy:
        for ln in wrap_text(brand.return_policy, width_chars):
            b += esc_line(ln)

    for ln in brand.footer_lines:
        for wln in wrap_text(ln, width_chars):
            b += esc_line(wln)

    if brand.social:
        b += esc_line(brand.social)

    if brand.qr_text:
        b += esc_line("")
        for ln in wrap_text(brand.qr_text, width_chars):
            b += esc_line(ln)

    b += esc_feed(4)
    b += esc_cut()
    return bytes(b)


# -----------------------------
# PDF preview (no printer needed)
# -----------------------------
def preview_receipt_pdf(
    order: ReceiptOrder,
    brand: BrandHeaderFooter,
    width_mm: float = 80.0
) -> str:
    # Typical thermal widths: 58mm or 80mm. We'll render on 80mm by default.
    # Height is dynamic.
    line_height = 4.0 * mm
    margin = 4 * mm
    width = width_mm * mm

    # Rough line count estimate
    lines = []
    lines.append(brand.brand_name)
    if brand.slogan: lines.append(brand.slogan)
    if brand.mall_name: lines.append(brand.mall_name)
    lines += brand.address_lines
    if brand.phone: lines.append(f"Tel: {brand.phone}")
    if brand.website: lines.append(brand.website)
    if brand.tax_id: lines.append(f"Tax ID: {brand.tax_id}")
    lines.append("-" * 32)
    lines.append(f"Invoice: {order.invoice_no}")
    lines.append(f"Date: {order.datetime_local.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Cashier: {order.cashier}")
    if order.customer: lines.append(f"Customer: {order.customer}")
    lines.append("-" * 32)

    for it in order.items:
        lines.append(it.name)
        lines.append(f"{it.qty:g} x {money(it.price)} {order.currency}   =   {money(it.total)} {order.currency}")
        if it.sku: lines.append(f"SKU: {it.sku}")
        lines.append("")

    lines.append("-" * 32)
    lines.append(f"Subtotal: {money(order.subtotal)} {order.currency}")
    if order.discount > 0:
        lines.append(f"Discount: -{money(order.discount)} {order.currency}")
    if order.tax_rate > 0:
        lines.append(f"Tax ({order.tax_rate*100:.0f}%): {money(order.tax_amount)} {order.currency}")
    lines.append(f"TOTAL: {money(order.total)} {order.currency}")
    lines.append("-" * 32)
    lines.append(f"Payment: {order.payment_method}")
    if order.amount_paid > 0:
        lines.append(f"Paid: {money(order.amount_paid)} {order.currency}")
        lines.append(f"Change: {money(order.change)} {order.currency}")
    lines.append("-" * 32)
    lines.append(brand.thank_you)
    lines.append(brand.return_policy)
    lines += brand.footer_lines
    if brand.social: lines.append(brand.social)
    if brand.qr_text: lines.append(brand.qr_text)

    height = margin * 2 + line_height * (len(lines) + 4)
    pdf_path = os.path.join(tempfile.gettempdir(), f"receipt_preview_{order.invoice_no}.pdf")

    c = canvas.Canvas(pdf_path, pagesize=(width, height))
    y = height - margin
    c.setFont("Courier", 9)

    for ln in lines:
        # wrap long lines
        max_chars = 32  # approx for Courier 9 on 80mm; adjust if needed
        chunks = wrap_text(ln, max_chars) if len(ln) > max_chars else [ln]
        for ch in chunks:
            c.drawString(margin, y, ch)
            y -= line_height

    c.showPage()
    c.save()
    return pdf_path


# -----------------------------
# Main: detect -> print OR preview
# -----------------------------
def print_receipt(
    order: ReceiptOrder,
    brand: BrandHeaderFooter,
    printer_name: Optional[str] = None,
    width_chars: int = 42,
    preview_only: bool = False
) -> Dict[str, str]:
    printers = detect_printers()

    # Allow override from ENV as well
    env_printer = os.getenv("THERMAL_PRINTER_NAME", "").strip()
    if not printer_name and env_printer:
        printer_name = env_printer

    chosen = printer_name or pick_best_printer(printers)

    # Build ESC/POS data
    data = build_receipt_escpos(order, brand, width_chars=width_chars)

    # If preview only or no printer found => PDF preview
    if preview_only or not chosen:
        pdf = preview_receipt_pdf(order, brand, width_mm=80.0)
        return {
            "status": "preview",
            "pdf": pdf,
            "printer": chosen or "",
            "detected_printers": ", ".join(printers)
        }

    # Try printing
    send_raw_to_printer(chosen, data)
    return {
        "status": "printed",
        "printer": chosen,
        "detected_printers": ", ".join(printers)
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Thermal receipt printing with auto-detect + PDF preview fallback")
    parser.add_argument("--printer", help="Exact printer name to use (overrides auto-detect)", default=None)
    parser.add_argument("--preview", help="Generate PDF preview instead of printing", action="store_true")
    parser.add_argument("--width", help="Receipt width in characters (usually 32 for 58mm, 42 for 80mm)", type=int, default=42)
    args = parser.parse_args()

    # ---- Example data (replace with your bill/order data) ----
    brand = BrandHeaderFooter(
        brand_name="QUICKMART",
        slogan="Smart Shopping. Better Living.",
        mall_name="Kabul City Center - Ground Floor",
        address_lines=[
            "Shop #12, Main Hall",
            "Kabul, Afghanistan"
        ],
        phone="+93 70 000 0000",
        website="www.quickmart.af",
        tax_id="TIN: 123456789",
        return_policy="Return/exchange within 7 days with receipt. Items must be unopened and in original condition.",
        footer_lines=[
            "For support: support@quickmart.af",
            "Working Hours: 9:00 AM - 9:00 PM"
        ],
        social="@quickmart.af",
        qr_text="Scan to join our loyalty program (QR shown in app)."
    )

    order = ReceiptOrder(
        invoice_no="INV-2026-001",
        datetime_local=datetime.now(),
        cashier="Noorullah",
        customer="Walk-in",
        items=[
            ReceiptItem(name="Coca Cola 330ml", qty=2, price=30.0, sku="CC330"),
            ReceiptItem(name="Lays Chips (Large)", qty=1, price=50.0, sku="LYS-L"),
            ReceiptItem(name="Chocolate Bar Extra Dark 85% (Imported)", qty=1, price=120.0, sku="CH-85")
        ],
        discount=10.0,
        tax_rate=0.00,   # set 0.10 for 10% etc.
        currency="AFN",
        payment_method="Cash",
        amount_paid=300.0
    )

    result = print_receipt(
        order=order,
        brand=brand,
        printer_name=args.printer,
        width_chars=args.width,
        preview_only=args.preview
    )

    print("Result:", result)
    if result["status"] == "preview":
        print("Preview PDF:", result["pdf"])
        # You can open it automatically if you want:
        # os.startfile(result["pdf"])  # Windows only
