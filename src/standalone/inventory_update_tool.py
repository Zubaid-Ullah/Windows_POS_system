import sys
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox)
from PyQt6.QtCore import Qt
import sqlite3
import os

class InventoryUpdater(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FaqiriTech Inventory Sync Tool")
        self.setMinimumSize(600, 400)
        self.main_db = os.path.join("..", "..", "pos_system.db") if os.path.exists(os.path.join("..", "..", "pos_system.db")) else "pos_system.db"
        self.local_db = "update_inventory.db"
        self._init_local_db()
        self.init_ui()

    def _init_local_db(self):
        # Create a sample local DB if not exists
        conn = sqlite3.connect(self.local_db)
        conn.execute("CREATE TABLE IF NOT EXISTS local_products (barcode TEXT PRIMARY KEY, qty REAL)")
        # Sample data
        conn.execute("INSERT OR IGNORE INTO local_products VALUES ('123456', 50)")
        conn.commit()
        conn.close()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<h3>Inventory Update Tool</h3>"))
        layout.addWidget(QLabel("Merge products from internal database to main POS system."))
        
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Barcode", "New Quantity"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        
        self.load_local()
        
        btn = QPushButton("Update Main Inventory")
        btn.setFixedHeight(45)
        btn.clicked.connect(self.sync)
        layout.addWidget(btn)

    def load_local(self):
        conn = sqlite3.connect(self.local_db)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM local_products")
        rows = cursor.fetchall()
        self.table.setRowCount(0)
        for i, row in enumerate(rows):
            self.table.insertRow(i)
            self.table.setItem(i, 0, QTableWidgetItem(row[0]))
            self.table.setItem(i, 1, QTableWidgetItem(str(row[1])))
        conn.close()

    def sync(self):
        try:
            conn_local = sqlite3.connect(self.local_db)
            cursor_local = conn_local.cursor()
            cursor_local.execute("SELECT * FROM local_products")
            updates = cursor_local.fetchall()
            
            conn_main = sqlite3.connect(self.main_db)
            cursor_main = conn_main.cursor()
            
            count = 0
            for barcode, qty in updates:
                # Find product in main
                cursor_main.execute("SELECT id FROM products WHERE barcode = ?", (barcode,))
                res = cursor_main.fetchone()
                if res:
                    pid = res[0]
                    cursor_main.execute("UPDATE inventory SET quantity = quantity + ? WHERE product_id = ?", (qty, pid))
                    count += 1
            
            conn_main.commit()
            conn_main.close()
            conn_local.close()
            QMessageBox.information(self, "Success", f"Synced {count} products to main inventory.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Update failed: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = InventoryUpdater()
    window.show()
    sys.exit(app.exec())
