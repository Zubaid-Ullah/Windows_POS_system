from PyQt6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, QVariantAnimation
from PyQt6.QtGui import QColor
import qtawesome as qta
from src.ui.theme_manager import theme_manager

class StatCard(QFrame):
    def __init__(self, title, value, subtext="", icon_name="fa5s.chart-bar", icon_color="#4318ff"):
        super().__init__()
        self.setObjectName("card")
        self.setMinimumHeight(120)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Icon Container
        icon_bg = QFrame()
        icon_bg.setFixedSize(50, 50)
        try:
            curr_color = QColor(icon_color)
            icon_bg.setStyleSheet(f"background-color: {curr_color.lighter(180).name()}; border-radius: 25px; border: none;")
        except:
            icon_bg.setStyleSheet(f"background-color: #f4f7fe; border-radius: 25px; border: none;")
            
        icon_layout = QVBoxLayout(icon_bg)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_lbl = QLabel()
        icon_lbl.setPixmap(qta.icon(icon_name, color=icon_color).pixmap(24, 24))
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_layout.addWidget(icon_lbl)
        
        # Text Info
        text_layout = QVBoxLayout()
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("color: #a3aed0; font-size: 14px; font-weight: 500; border: none; background: transparent;")
        
        v_color = "#ffffff" if theme_manager.is_dark else "#1b2559"
        self.value_lbl = QLabel(value)
        self.value_lbl.setFixedHeight(35)
        self.value_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.value_lbl.setStyleSheet(f"color: {v_color}; font-size: 24px; font-weight: bold; border: none; background: transparent;")
        
        self.sub_lbl = QLabel(subtext)
        self.sub_lbl.setStyleSheet("color: #a3aed0; font-size: 12px; border: none; background: transparent;")
        
        text_layout.addWidget(title_lbl)
        text_layout.addWidget(self.value_lbl)
        text_layout.addWidget(self.sub_lbl)
        
        layout.addWidget(icon_bg)
        layout.addLayout(text_layout)
        layout.addStretch()
        
        # Hover Animation
        self.hover_anim = QVariantAnimation()
        self.hover_anim.setDuration(400)
        self.hover_anim.setStartValue(QColor(255, 255, 255, 0))
        self.hover_anim.setEndValue(QColor(255, 255, 255, 20))
        self.hover_anim.valueChanged.connect(self.update)

    def paintEvent(self, event):
        from PyQt6.QtGui import QPainter
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), self.hover_anim.currentValue())
        super().paintEvent(event)

    def enterEvent(self, event):
        self.hover_anim.setDirection(QVariantAnimation.Direction.Forward)
        self.hover_anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.hover_anim.setDirection(QVariantAnimation.Direction.Backward)
        self.hover_anim.start()
        super().leaveEvent(event)

    def update_data(self, value, subtext=None):
        self.value_lbl.setText(value)
        if subtext is not None:
            self.sub_lbl.setText(subtext)

    def update_value(self, value):
        """Backward compatibility for calls only updating value"""
        self.update_data(value)
