import sys
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLineEdit, 
                             QPushButton, QLabel, QDateTimeEdit, QMessageBox, QFrame)
from PyQt6.QtCore import Qt, QDateTime
import sqlite3
import os

class ActivationTool(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Afex System Activation")
        self.setFixedSize(400, 500)
        self.db_path = os.path.join("..", "..", "pos_system.db") if os.path.exists(os.path.join("..", "..", "pos_system.db")) else "pos_system.db"
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        
        layout.addWidget(QLabel("<h2>System Activation</h2>"))
        layout.addWidget(QLabel("Connect to central server to authorize usage."))
        
        self.user = QLineEdit()
        self.user.setPlaceholderText("Online Username")
        self.pwd = QLineEdit()
        self.pwd.setPlaceholderText("Online Password")
        self.pwd.setEchoMode(QLineEdit.EchoMode.Password)
        
        layout.addWidget(self.user)
        layout.addWidget(self.pwd)
        
        layout.addSpacing(20)
        layout.addWidget(QLabel("<b>License Period:</b>"))
        self.target_date = QDateTimeEdit(QDateTime.currentDateTime().addYears(1))
        self.target_date.setCalendarPopup(True)
        layout.addWidget(self.target_date)
        
        layout.addStretch()
        
        btn = QPushButton("Activate System")
        btn.setFixedHeight(45)
        btn.setStyleSheet("background-color: #4318ff; color: white; font-weight: bold; border-radius: 10px;")
        btn.clicked.connect(self.activate)
        layout.addWidget(btn)

    def activate(self):
        # Simulating online check
        user = self.user.text()
        pwd = self.pwd.text()
        if not user or not pwd:
            QMessageBox.warning(self, "Error", "Credentials required")
            return
            
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE IF NOT EXISTS app_settings (key TEXT PRIMARY KEY, value TEXT)")
            cursor.execute("INSERT OR REPLACE INTO app_settings (key, value) VALUES ('contract_end', ?)", 
                         (self.target_date.dateTime().toString("yyyy-MM-dd"),))
            conn.commit()
            conn.close()
            QMessageBox.information(self, "Activated", "System activated successfully until " + self.target_date.dateTime().toString("yyyy-MM-dd"))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not access database: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ActivationTool()
    window.show()
    sys.exit(app.exec())
