"""
Premium Button Styling System for POS
Provides consistent, modern button aesthetics with HCI best practices
"""

from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

class ButtonStyler:
    """Centralized button styling following Material Design principles"""
    
    # Color palette
    COLORS = {
        'primary': '#2196f3',      # Blue - main actions
        'primary_hover': '#1976d2',
        'primary_pressed': '#0d47a1',
        
        'success': '#4caf50',      # Green - positive actions
        'success_hover': '#388e3c',
        'success_pressed': '#1b5e20',
        
        'danger': '#f44336',       # Red - destructive actions
        'danger_hover': '#d32f2f',
        'danger_pressed': '#b71c1c',
        
        'warning': '#ff9800',      # Orange - caution
        'warning_hover': '#f57c00',
        'warning_pressed': '#e65100',
        
        'secondary': '#607d8b',    # Gray - secondary actions
        'secondary_hover': '#455a64',
        'secondary_pressed': '#263238',
        
        'info': '#00bcd4',         # Cyan - informational
        'info_hover': '#0097a7',
        'info_pressed': '#006064',
    }
    
    @staticmethod
    def _get_base_style(bg_color, hover_color, pressed_color, text_color='white'):
        """Generate base button stylesheet"""
        return f"""
            QPushButton {{
                background-color: {bg_color};
                color: {text_color};
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: 600;
                min-height: 36px;
            }}
            
            QPushButton:hover {{
                background-color: {hover_color};
            }}
            
            QPushButton:pressed {{
                background-color: {pressed_color};
            }}
            
            QPushButton:disabled {{
                background-color: #e0e0e0;
                color: #9e9e9e;
            }}
        """
    
    @staticmethod
    def apply_primary_style(button: QPushButton):
        """Blue button for primary actions (Save, Submit, Confirm)"""
        button.setStyleSheet(ButtonStyler._get_base_style(
            ButtonStyler.COLORS['primary'],
            ButtonStyler.COLORS['primary_hover'],
            ButtonStyler.COLORS['primary_pressed']
        ))
        button.setCursor(Qt.CursorShape.PointingHandCursor)
    
    @staticmethod
    def apply_success_style(button: QPushButton):
        """Green button for positive actions (Add, Create, Complete)"""
        button.setStyleSheet(ButtonStyler._get_base_style(
            ButtonStyler.COLORS['success'],
            ButtonStyler.COLORS['success_hover'],
            ButtonStyler.COLORS['success_pressed']
        ))
        button.setCursor(Qt.CursorShape.PointingHandCursor)
    
    @staticmethod
    def apply_danger_style(button: QPushButton):
        """Red button for destructive actions (Delete, Remove, Cancel)"""
        button.setStyleSheet(ButtonStyler._get_base_style(
            ButtonStyler.COLORS['danger'],
            ButtonStyler.COLORS['danger_hover'],
            ButtonStyler.COLORS['danger_pressed']
        ))
        button.setCursor(Qt.CursorShape.PointingHandCursor)
    
    @staticmethod
    def apply_warning_style(button: QPushButton):
        """Orange button for caution actions (Reset, Clear)"""
        button.setStyleSheet(ButtonStyler._get_base_style(
            ButtonStyler.COLORS['warning'],
            ButtonStyler.COLORS['warning_hover'],
            ButtonStyler.COLORS['warning_pressed']
        ))
        button.setCursor(Qt.CursorShape.PointingHandCursor)
    
    @staticmethod
    def apply_secondary_style(button: QPushButton):
        """Gray button for secondary actions (Cancel, Back, Close)"""
        button.setStyleSheet(ButtonStyler._get_base_style(
            ButtonStyler.COLORS['secondary'],
            ButtonStyler.COLORS['secondary_hover'],
            ButtonStyler.COLORS['secondary_pressed']
        ))
        button.setCursor(Qt.CursorShape.PointingHandCursor)
    
    @staticmethod
    def apply_info_style(button: QPushButton):
        """Cyan button for informational actions (View, Details, Info)"""
        button.setStyleSheet(ButtonStyler._get_base_style(
            ButtonStyler.COLORS['info'],
            ButtonStyler.COLORS['info_hover'],
            ButtonStyler.COLORS['info_pressed']
        ))
        button.setCursor(Qt.CursorShape.PointingHandCursor)
    
    @staticmethod
    def apply_outline_style(button: QPushButton, color='primary'):
        """Outlined button variant for less prominent actions"""
        base_color = ButtonStyler.COLORS.get(color, ButtonStyler.COLORS['primary'])
        hover_color = ButtonStyler.COLORS.get(f'{color}_hover', ButtonStyler.COLORS['primary_hover'])
        
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {base_color};
                border: 2px solid {base_color};
                border-radius: 6px;
                padding: 8px 18px;
                font-size: 14px;
                font-weight: 600;
                min-height: 36px;
            }}
            
            QPushButton:hover {{
                background-color: {base_color};
                color: white;
            }}
            
            QPushButton:pressed {{
                background-color: {hover_color};
                color: white;
                border-color: {hover_color};
            }}
            
            QPushButton:disabled {{
                border-color: #e0e0e0;
                color: #9e9e9e;
            }}
        """)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
    
    @staticmethod
    def apply_icon_button_style(button: QPushButton, color='primary'):
        """Small icon-only button (for table actions)"""
        base_color = ButtonStyler.COLORS.get(color, ButtonStyler.COLORS['primary'])
        hover_color = ButtonStyler.COLORS.get(f'{color}_hover', ButtonStyler.COLORS['primary_hover'])
        
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {base_color};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 2px 4px;
                font-size: 12px;
                min-width: 28px;
                min-height: 28px;
            }}
            
            QPushButton:hover {{
                background-color: {hover_color};
            }}
            
            QPushButton:disabled {{
                background-color: #e0e0e0;
                color: #9e9e9e;
            }}
        """)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
    
    @staticmethod
    def apply_small_button_style(button: QPushButton, color='primary'):
        """Compact button with text (ideal for tables)"""
        base_color = ButtonStyler.COLORS.get(color, ButtonStyler.COLORS['primary'])
        hover_color = ButtonStyler.COLORS.get(f'{color}_hover', ButtonStyler.COLORS['primary_hover'])
        
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {base_color};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 13px;
                font-weight: 500;
                min-height: 28px;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
            QPushButton:disabled {{
                background-color: #e0e0e0;
                color: #9e9e9e;
            }}
        """)
        button.setCursor(Qt.CursorShape.PointingHandCursor)

    @staticmethod
    def apply_large_button_style(button: QPushButton, color='primary'):
        """Large prominent button for critical actions"""
        base_color = ButtonStyler.COLORS.get(color, ButtonStyler.COLORS['primary'])
        hover_color = ButtonStyler.COLORS.get(f'{color}_hover', ButtonStyler.COLORS['primary_hover'])
        pressed_color = ButtonStyler.COLORS.get(f'{color}_pressed', ButtonStyler.COLORS['primary_pressed'])
        
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {base_color};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 16px 32px;
                font-size: 16px;
                font-weight: 700;
                min-height: 50px;
            }}
            
            QPushButton:hover {{
                background-color: {hover_color};
            }}
            
            QPushButton:pressed {{
                background-color: {pressed_color};
            }}
            
            QPushButton:disabled {{
                background-color: #e0e0e0;
                color: #9e9e9e;
            }}
        """)
        button.setCursor(Qt.CursorShape.PointingHandCursor)


# Convenience functions for quick styling
def style_button(button: QPushButton, variant='primary', size='normal'):
    """
    Quick button styling function
    
    Args:
        button: QPushButton to style
        variant: 'primary', 'success', 'danger', 'warning', 'secondary', 'info', 'outline'
        size: 'normal', 'large', 'icon'
    """
    if size == 'large':
        ButtonStyler.apply_large_button_style(button, variant if variant != 'outline' else 'primary')
    elif size == 'small':
        ButtonStyler.apply_small_button_style(button, variant if variant != 'outline' else 'primary')
    elif size == 'icon':
        ButtonStyler.apply_icon_button_style(button, variant if variant != 'outline' else 'primary')
    elif variant == 'outline':
        ButtonStyler.apply_outline_style(button)
    elif variant == 'success':
        ButtonStyler.apply_success_style(button)
    elif variant == 'danger':
        ButtonStyler.apply_danger_style(button)
    elif variant == 'warning':
        ButtonStyler.apply_warning_style(button)
    elif variant == 'secondary':
        ButtonStyler.apply_secondary_style(button)
    elif variant == 'info':
        ButtonStyler.apply_info_style(button)
    else:
        ButtonStyler.apply_primary_style(button)
