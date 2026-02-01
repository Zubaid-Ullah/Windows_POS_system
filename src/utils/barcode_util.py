import barcode
from barcode.writer import ImageWriter
import os

class BarcodeGenerator:
    @staticmethod
    def generate(code, filename):
        try:
            EAN = barcode.get_barcode_class('code128')
            ean = EAN(code, writer=ImageWriter())
            fullname = ean.save(filename)
            return fullname
        except Exception as e:
            print(f"Error generating barcode: {e}")
            return None

    @staticmethod
    def get_supported_formats():
        return barcode.PROVIDED_BARCODES
