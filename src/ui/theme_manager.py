from PyQt6.QtCore import QObject, pyqtSignal, QTimer
import sys

class ThemeManager(QObject):
    theme_changed = pyqtSignal(bool)
    
    # QuickMart Premium Palette (Matched to Reference Image)
    QUICKMART = {
        "sidebar_bg": "#1a3a8a",
        "sidebar_hover": "#254db1",
        "sidebar_active": "#102a63",
        "sidebar_text": "#ffffff",
        "sidebar_inactive": "#a5b4fc",
        
        "bg_main": "#f4f7fe",
        "bg_card": "#ffffff",
        "text_main": "#000000",
        "text_secondary": "#475569",
        
        "primary": "#4318ff",
        "success": "#05cd99",
        "danger": "#ee5d50",
        "warning": "#ffb547",
        "info": "#01b9ff",
        
        "border": "#e0e5f2",
        "shadow": "rgba(112, 144, 176, 0.1)"
    }
    # Dark Mode Palette
    DARK = {
        "sidebar_bg": "#1a3a8a",
        "sidebar_hover": "#254db1",
        "sidebar_active": "#102a63",
        "sidebar_text": "#ffffff",
        "sidebar_inactive": "#a5b4fc",
        
        "bg_main": "#0b1437",
        "bg_card": "#111c44",
        "text_main": "#ffffff",
        "text_secondary": "#a3aed0",
        
        "primary": "#7551ff",
        "success": "#05cd99",
        "danger": "#ee5d50",
        "warning": "#ffb547",
        "info": "#01b9ff",
        
        "border": "#1b2559",
        "shadow": "rgba(0, 0, 0, 0.3)"
    }
    
    _instance = None
    def __init__(self):
        super().__init__()
        self.is_dark = False
        self.theme_mode = "LIGHT" # LIGHT, DARK, or SYSTEM

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def init_theme(self):
        """Load saved theme and apply it."""
        from src.database.db_manager import db_manager
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM app_settings WHERE key = 'theme_mode'")
            row = cursor.fetchone()
            if row:
                self.theme_mode = row['value']
            else:
                self.theme_mode = "SYSTEM"
        
        self._apply_mode()
        
        # Monitor for real-time changes
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self._apply_mode)
        self.monitor_timer.start(2000) # Check every 2 seconds for zero-restart experience

    def toggle_theme(self):
        self.is_dark = not self.is_dark
        self.theme_changed.emit(self.is_dark)
        return self.is_dark

    def set_dark_mode(self, enabled):
        # Compatibility for old calls
        self.theme_mode = "DARK" if enabled else "LIGHT"
        self._apply_mode()

    def set_theme_mode(self, mode):
        self.theme_mode = mode
        self._apply_mode()
        
        # Save to DB
        from src.database.db_manager import db_manager
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO app_settings (key, value) VALUES ('theme_mode', ?)", (mode,))
            conn.commit()

    def _apply_mode(self):
        target_dark = False
        if self.theme_mode == "SYSTEM":
            # Better cross-platform detection
            if sys.platform == "darwin":
                # macOS Specific detection via palette lightness
                from PyQt6.QtWidgets import QApplication
                from PyQt6.QtGui import QPalette
                if QApplication.instance():
                    palette = QApplication.instance().palette()
                    base_color = palette.color(QPalette.ColorRole.Window)
                    target_dark = base_color.lightness() < 128
            elif sys.platform == "win32":
                try:
                    import winreg
                    registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
                    key = winreg.OpenKey(registry, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
                    value, regtype = winreg.QueryValueEx(key, "AppsUseLightTheme")
                    target_dark = value == 0
                except:
                    target_dark = False
            else:
                # Fallback for others
                from PyQt6.QtWidgets import QApplication
                from PyQt6.QtGui import QPalette
                if QApplication.instance():
                    palette = QApplication.instance().palette()
                    target_dark = palette.color(QPalette.ColorRole.Window).lightness() < 128
        else:
            target_dark = (self.theme_mode == "DARK")
            
        if self.is_dark != target_dark:
            self.is_dark = target_dark
            self.theme_changed.emit(self.is_dark)

    def get_style(self):
        t = self.DARK if self.is_dark else self.QUICKMART
        scroll_bg = "#1b2559" if self.is_dark else "#e2e8f0"
        scroll_handle = "#4318ff" if self.is_dark else "#94a3b8"
        
        return f"""
        * {{
            font-family: 'Arial';
        }}

        QMainWindow, QDialog, QWidget {{
            background-color: {t['bg_main']};
            color: {t['text_main']};
            font-family: 'Arial';
        }}
        
        QFrame#sidebar {{
            background-color: {t['sidebar_bg']};
            border: none;
        }}
        
        QLabel#logo_text {{
            color: #ffffff;
            font-size: 20px;
            font-weight: bold;
            border: none;
            background: transparent;
            margin-left: 5px;
        }}
        
        QPushButton#menu_button {{
            background-color: transparent;
            color: {t['sidebar_inactive']};
            text-align: left;
            padding: 15px 25px;
            border: none;
            font-size: 14px;
            font-weight: 600;
            border-left: 5px solid transparent;
            margin: 2px 0px;
        }}
        
        QPushButton#menu_button:hover {{
            background-color: {t['sidebar_hover']};
            color: white;
        }}
        
        QPushButton#menu_button:checked {{
            background-color: {t['sidebar_active']};
            color: white;
            font-weight: 700;
            border-left: 5px solid #ffffff;
        }}
        
        QPushButton#sub_menu_button {{
            background-color: transparent;
            color: {t['sidebar_inactive']};
            text-align: left;
            padding: 8px 12px 8px 30px;
            border: none;
            font-size: 12px;
        }}
        
        QPushButton#sub_menu_button:hover {{
            background-color: {t['sidebar_hover']};
            color: white;
        }}
        
        QPushButton#sub_menu_button:checked {{
            background-color: {t['sidebar_active']};
            color: white;
            font-weight: 600;
        }}
        
        QFrame#content_area {{
            background-color: {t['bg_main']};
            border: none;
        }}
        
        QLabel#page_header {{
            font-size: 24px;
            font-weight: bold;
            color: {t['text_main']};
            background: transparent;
            border: none;
        }}
        
        QScrollArea {{
            background: transparent;
            border: none;
        }}
        
        QScrollArea > QWidget > QWidget {{
            background: transparent;
        }}

        QLineEdit, QComboBox, QDateEdit, QTextEdit, QSpinBox, QDoubleSpinBox {{
            padding: 10px 15px;
            border: none;
            border-radius: 8px;
            background-color: {t['bg_card']} !important;
            color: {t['text_main']} !important;
            font-size: 18px;
        }}
        
        QSpinBox::up-button, QSpinBox::down-button {{
            background-color: transparent;
            border: none;
        }}
        
        QSpinBox QLineEdit {{
            background-color: transparent !important;
            color: {t['text_main']} !important;
        }}
        
        QLineEdit[background="black"], QComboBox[background="black"] {{
            color: #ffffff !important;
        }}
        
        QLineEdit[readOnly="true"] {{
            background-color: {t['bg_main']};
            color: {t['text_main']};
            opacity: 0.8;
            border: 1px solid {t['border']};
        }}

        QLineEdit::placeholder {{
            color: {'#94a3b8' if not self.is_dark else '#64748b'};
        }}
        
        QLineEdit:focus, QComboBox:focus {{
            border: 2px solid {t['primary']};
        }}
        
        QTableWidget {{
            background-color: {t['bg_card']};
            border: none;
            gridline-color: {t['border']};
            border-radius: 12px;
            outline: none;
            color: {t['text_main']};
        }}
        
        QTableWidget::item {{
            color: {t['text_main']};
            padding: 8px;
        }}
        
        QHeaderView::section {{
            background-color: {t['sidebar_bg']};
            color: #ffffff;
            padding: 12px;
            border: none;
            font-weight: bold;
            font-size: 11px;
            text-transform: uppercase;
        }}
        
        QComboBox QAbstractItemView {{
            background-color: {t['bg_card']};
            color: {t['text_main']};
            border: none;
            selection-background-color: {t['primary']};
            selection-color: #ffffff;
            outline: none;
        }}
        
        QComboBox QAbstractItemView::item {{
            padding: 10px;
            background-color: transparent;
        }}

        QComboBox QAbstractItemView::item:hover {{
            background-color: {t['sidebar_hover']};
            color: #ffffff;
        }}

        QComboBox QAbstractItemView::item:selected {{
            background-color: {t['primary']};
            color: #ffffff;
        }}
        
        QLabel {{
            color: {t['text_main']};
            background: none;
        }}
        
        QFrame#card {{
            background-color: {t['bg_card']};
            border-radius: 16px;
            border: none;
        }}
        
        QLabel#stat_title {{
            color: {'#94a3b8' if not self.is_dark else '#a3aed0'};
            font-size: 14px;
            font-weight: 500;
            border: none;
            background: transparent;
        }}
        
        QLabel#stat_value {{
            color: {t['text_main']};
            font-size: 24px;
            font-weight: bold;
            border: none;
            background: transparent;
        }}
        
        QGroupBox {{
            background-color: {t['bg_card']};
            border: none;
            border-radius: 12px;
            padding: 15px;
            margin-top: 10px;
            font-weight: bold;
            color: {t['text_main']};
        }}
        
        QScrollBar:vertical {{
            border: none;
            background: {scroll_bg};
            width: 8px;
            border-radius: 4px;
        }}
        
        QScrollBar::handle:vertical {{
            background: {scroll_handle};
            border-radius: 4px;
        }}
        
        QScrollBar:horizontal {{
            border: none;
            background: {scroll_bg};
            height: 8px;
            border-radius: 4px;
        }}
        
        QScrollBar::handle:horizontal {{
            background: {scroll_handle};
            border-radius: 4px;
        }}
        
        QMessageBox {{
            background-color: {t['bg_card']};
        }}
        
        QMessageBox QLabel {{
            color: {t['text_main']};
        }}
        
        QPushButton {{
            border: none;
        }}
        """

theme_manager = ThemeManager.get_instance()
