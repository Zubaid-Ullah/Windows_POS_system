from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QProgressBar)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
import qtawesome as qta
from src.core.supabase_manager import supabase_manager
from src.ui.theme_manager import theme_manager
from src.ui.button_styles import style_button

class ConnectivityGateWindow(QWidget):
    connection_resolved = pyqtSignal(bool) # True if online

    def __init__(self):
        super().__init__()
        self.setWindowTitle("AFEX POS System Check")
        self.setFixedSize(450, 420)
        self.init_ui()
        
    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(40, 40, 40, 40)
        self.layout.setSpacing(20)
        
        self.setStyleSheet(f"background-color: {'#ffffff' if not theme_manager.is_dark else '#111c44'};")
        
        self.icon_lbl = QLabel()
        self.icon_lbl.setPixmap(qta.icon("fa5s.wifi", color="#4318ff").pixmap(60, 60))
        self.icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.icon_lbl)
        
        self.title_lbl = QLabel("Checking Internet...")
        self.title_lbl.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {'#1b2559' if not theme_manager.is_dark else '#ffffff'};")
        self.title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.title_lbl)
        
        self.status_lbl = QLabel("Verifying secure cloud gateway...")
        self.status_lbl.setStyleSheet("font-size: 13px; color: #a3aed0;")
        self.status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_lbl.setWordWrap(True)
        self.layout.addWidget(self.status_lbl)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setFixedHeight(4)
        self.progress.setTextVisible(False)
        self.progress.setStyleSheet("QProgressBar { border: none; background: #e0e5f2; border-radius: 2px; } QProgressBar::chunk { background-color: #4318ff; }")
        self.layout.addWidget(self.progress)
        
        # Action Buttons
        self.btn_lay = QHBoxLayout()
        self.retry_btn = QPushButton(" Retry Connection")
        style_button(self.retry_btn, variant="primary")
        self.retry_btn.clicked.connect(self.check_now)
        self.retry_btn.hide()
        
        self.btn_lay.addWidget(self.retry_btn)
        
        self.offline_btn = QPushButton(" Continue Offline")
        style_button(self.offline_btn, variant="outline")
        self.offline_btn.clicked.connect(self.go_offline)
        self.offline_btn.hide()
        self.btn_lay.addWidget(self.offline_btn)
        
        self.layout.addLayout(self.btn_lay)

        QTimer.singleShot(100, self.check_now)

    def check_now(self):
        self.retry_btn.hide()
        self.offline_btn.hide()
        self.progress.show()
        self.title_lbl.setText("Checking Internet...")
        self.icon_lbl.setPixmap(qta.icon("fa5s.wifi", color="#4318ff").pixmap(60, 60))
        
        from PyQt6.QtCore import QThread
        class CheckThread(QThread):
            res = pyqtSignal(bool)
            def run(self):
                online = supabase_manager.check_connection()
                self.res.emit(online)

        self.check_thread = CheckThread()
        self.check_thread.res.connect(self._on_check_finished)
        self.check_thread.start()

    def _on_check_finished(self, is_online):
        print(f"\n[CONNECTIVITY_GATE] _on_check_finished called: is_online={is_online}")
        self.progress.hide()
        if is_online:
            print("[CONNECTIVITY_GATE] Connection successful, updating UI...")
            self.title_lbl.setText("Connection Secure")
            self.title_lbl.setStyleSheet("color: #10b981; font-weight: bold; font-size: 20px;")
            self.icon_lbl.setPixmap(qta.icon("fa5s.check-circle", color="#10b981").pixmap(60, 60))
            self.status_lbl.setText("Cloud link active. Syncing data...")
            print("[CONNECTIVITY_GATE] Scheduling connection_resolved signal emission in 1 second...")
            QTimer.singleShot(1000, lambda: self._emit_resolved(True))
        else:
            print("[CONNECTIVITY_GATE] Connection failed, showing retry options...")
            self.title_lbl.setText("No Internet Connection")
            self.title_lbl.setStyleSheet("color: #ee5d50; font-weight: bold; font-size: 20px;")
            self.icon_lbl.setPixmap(qta.icon("fa5s.exclamation-triangle", color="#ee5d50").pixmap(60, 60))
            self.status_lbl.setText("An active internet connection is required to use the system. Please check your network and try again.")
            self.status_lbl.setText("An active internet connection is required to use the system. Please check your network and try again.")
            self.retry_btn.show()
            self.offline_btn.show()
    
    def _emit_resolved(self, online):
        print(f"[CONNECTIVITY_GATE] Emitting connection_resolved signal: online={online}")
        self.connection_resolved.emit(online)
        print("[CONNECTIVITY_GATE] Signal emitted successfully")

    def go_offline(self):
        self.connection_resolved.emit(False)
