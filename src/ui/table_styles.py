"""
Premium Table Styling Module for POS System
Provides consistent, modern table aesthetics across all views
"""

from PyQt6.QtWidgets import QTableWidget, QHeaderView
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

class TableStyler:
    """Centralized table styling with HCI best practices"""
    
    @staticmethod
    def apply_premium_style(table: QTableWidget, enable_alternating=True, enable_hover=True):
        """
        Apply premium styling to any QTableWidget
        
        Args:
            table: The QTableWidget to style
            enable_alternating: Enable alternating row colors for better readability
            enable_hover: Enable hover effects for better interaction feedback
        """
        
        # Base table configuration
        table.setAlternatingRowColors(enable_alternating)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        table.setShowGrid(False)  # Modern flat design
        table.setWordWrap(False)
        table.setCornerButtonEnabled(False)
        
        table_font = QFont()
        table_font.setFamily("Arial")
        table_font.setPointSize(18)
        table_font.setWeight(QFont.Weight.Normal)
        table.setFont(table_font)
        table.setEditTriggers(QTableWidget.EditTrigger.DoubleClicked | QTableWidget.EditTrigger.EditKeyPressed)
        
        # Header configuration
        header = table.horizontalHeader()
        header.setMinimumSectionSize(100) # Ensure headers are not too squashed
        header.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        
        # Initial sizing
        table.resizeColumnsToContents()
        table.resizeRowsToContents()
        
        # Vertical header (row numbers)
        v_header = table.verticalHeader()
        v_header.setVisible(False)  # Cleaner look
        v_header.setDefaultSectionSize(60)  # Appropriate for 18pt font
        
        from src.ui.theme_manager import theme_manager
        t = theme_manager.DARK if theme_manager.is_dark else theme_manager.QUICKMART
        
        # Premium stylesheet
        hover_bg = "#4318ff" if theme_manager.is_dark else "#e3f2fd"
        hover_text = "#ffffff" if theme_manager.is_dark else "#1565c0"
        alt_bg = "rgba(255, 255, 255, 0.05)" if theme_manager.is_dark else "#f8f9fa"
        if theme_manager.is_dark:
             alt_bg = "#161d31" # Balanced dark alternate row
        
        hover_style = f"""
            QTableWidget::item:hover {{
                background-color: {hover_bg};
                color: {hover_text};
            }}
        """ if enable_hover else ""
        
        table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {t['bg_card']};
                border: 1px solid {t['border']};
                border-radius: 8px;
                gridline-color: {t['border']};
                outline: none;
                color: {t['text_main']};
            }}
            
            QTableWidget::item {{
                padding: 8px 15px;
                border: none;
                color: {t['text_main']};
            }}
            
            QTableWidget::item:selected {{
                background-color: {t['primary']};
                color: white;
                font-weight: 500;
            }}
            
            {hover_style}
            
            QTableWidget::item:alternate {{
                background-color: {alt_bg};
            }}
            
            QHeaderView::section {{
                background-color: {t['sidebar_bg']};
                color: white;
                padding: 15px 15px;
                border: none;
                font-weight: 600;
                font-size: 18px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            
            QHeaderView::section:first {{
                border-top-left-radius: 8px;
            }}
            
            QHeaderView::section:last {{
                border-top-right-radius: 8px;
            }}
            
            QHeaderView::section:hover {{
                background-color: {t['sidebar_hover']};
            }}
            
            QScrollBar:vertical {{
                border: none;
                background: {t['bg_main']};
                width: 12px;
                border-radius: 6px;
            }}
            
            QScrollBar::handle:vertical {{
                background: {t['border']};
                border-radius: 6px;
                min-height: 30px;
            }}
            
            QScrollBar::handle:vertical:hover {{
                background: {t['primary']};
            }}
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            
            QScrollBar:horizontal {{
                border: none;
                background: {t['bg_main']};
                height: 12px;
                border-radius: 6px;
            }}
            
            QScrollBar::handle:horizontal {{
                background: {t['border']};
                border-radius: 6px;
                min-width: 30px;
            }}
            
            QScrollBar::handle:horizontal:hover {{
                background: {t['primary']};
            }}
            
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0px;
            }}
        """)
    
    @staticmethod
    def apply_compact_style(table: QTableWidget):
        """Compact variant for dense data displays"""
        TableStyler.apply_premium_style(table)
        v_header = table.verticalHeader()
        v_header.setDefaultSectionSize(50)
        
        table_font = QFont()
        table_font.setFamily("Arial")
        table_font.setPointSize(14)
        table.setFont(table_font)
        table.verticalHeader().setDefaultSectionSize(50)
    
    @staticmethod
    def apply_sales_cart_style(table: QTableWidget):
        """Special styling for sales cart with emphasis on readability"""
        TableStyler.apply_premium_style(table, enable_hover=True)
        
        # Even larger font for critical sales interaction
        table_font = QFont()
        table_font.setFamily("Arial")
        table_font.setPointSize(22)
        table_font.setWeight(QFont.Weight.Bold)
        table.setFont(table_font)
        
        v_header = table.verticalHeader()
        v_header.setDefaultSectionSize(80)
        
        # Enhanced visual feedback
        table.setStyleSheet(table.styleSheet() + """
            QTableWidget::item:selected {
                background-color: #4caf50;
                color: white;
                font-weight: 600;
            }
        """)

# Convenience function for quick application
def style_table(table: QTableWidget, variant="premium"):
    """
    Quick table styling function
    
    Args:
        table: QTableWidget to style
        variant: "premium", "compact", or "cart"
    """
    if variant == "compact":
        TableStyler.apply_compact_style(table)
    elif variant == "cart":
        TableStyler.apply_sales_cart_style(table)
    else:
        TableStyler.apply_premium_style(table)
