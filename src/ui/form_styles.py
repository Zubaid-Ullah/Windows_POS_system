"""
Standardized Form Styling for POS System
Provides consistent form layouts and input field styling
"""

from PyQt6.QtWidgets import QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit
from PyQt6.QtCore import Qt

class FormStyler:
    """Standardized form styling and layout utilities"""

    @staticmethod
    def style_input_field(widget, placeholder="", height=40):
        """Apply consistent styling to input fields"""
        if isinstance(widget, (QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit)):
            widget.setFixedHeight(height)

            if hasattr(widget, 'setPlaceholderText') and placeholder:
                widget.setPlaceholderText(placeholder)

            # Common styling
            widget.setStyleSheet(f"""
                padding: 8px 12px;
                border: 1px solid #ccc;
                border-radius: 6px;
                font-size: 13px;
                background-color: white;
                color: #333;
            """)

            widget.setStyleSheet(widget.styleSheet() + """
                :focus {
                    border-color: #4318ff;
                    outline: none;
                }
            """)

        return widget

    @staticmethod
    def style_form_group(group_box):
        """Apply consistent styling to form groups"""
        group_box.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #e0e5f2;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 15px;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px 0 10px;
                color: #4318ff;
                font-size: 14px;
            }
        """)
        return group_box

    @staticmethod
    def create_standard_form_layout():
        """Create a standard form layout with proper spacing"""
        from PyQt6.QtWidgets import QFormLayout
        layout = QFormLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        layout.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        return layout