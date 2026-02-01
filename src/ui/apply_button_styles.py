"""
Auto-apply premium button styling system-wide
Intelligently detects button types and applies appropriate styles
"""

import re
import os

# Button action keywords mapping to styles
BUTTON_PATTERNS = {
    'success': ['add', 'create', 'new', 'save', 'submit', 'confirm', 'complete', 'approve', 'accept'],
    'danger': ['delete', 'remove', 'cancel', 'reject', 'clear all', 'reset all'],
    'warning': ['reset', 'clear', 'undo', 'restore'],
    'info': ['view', 'details', 'info', 'show', 'display', 'search', 'lookup', 'check'],
    'secondary': ['close', 'back', 'cancel', 'skip'],
    'primary': ['update', 'edit', 'modify', 'change', 'refresh', 'reload', 'print', 'export', 'generate']
}

def detect_button_variant(button_text, button_var_name):
    """Detect appropriate button variant based on text/name"""
    text_lower = button_text.lower() + ' ' + button_var_name.lower()
    
    for variant, keywords in BUTTON_PATTERNS.items():
        for keyword in keywords:
            if keyword in text_lower:
                return variant
    
    return 'primary'  # Default

def add_button_styling_to_file(filepath):
    """Add button styling to a Python file"""
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if already has button styling import
    if 'from src.ui.button_styles import style_button' in content:
        print(f"✓ {filepath} already has button styling")
        return False
    
    # Find all QPushButton creations
    button_pattern = r'(self\.\w+)\s*=\s*QPushButton\(["\']([^"\']*)["\']?\)'
    matches = re.findall(button_pattern, content)
    
    if not matches:
        return False
    
    # Add import
    lines = content.split('\n')
    last_import_idx = 0
    for i, line in enumerate(lines):
        if line.startswith('import ') or line.startswith('from '):
            last_import_idx = i
    
    lines.insert(last_import_idx + 1, 'from src.ui.button_styles import style_button')
    
    # Process each button
    styled_count = 0
    for button_var, button_text in matches:
        variant = detect_button_variant(button_text, button_var)
        
        # Find button creation line and add styling after it
        for i, line in enumerate(lines):
            if f'{button_var} = QPushButton(' in line:
                # Look for the next line that's not a continuation
                insert_idx = i + 1
                while insert_idx < len(lines) and lines[insert_idx].strip().startswith('.'):
                    insert_idx += 1
                
                # Get indentation
                indent = len(line) - len(line.lstrip())
                style_line = ' ' * indent + f'style_button({button_var}, variant="{variant}")'
                
                # Check if not already styled
                if insert_idx < len(lines) and f'style_button({button_var}' not in lines[insert_idx]:
                    lines.insert(insert_idx, style_line)
                    styled_count += 1
                    print(f"  ✅ Styled {button_var} as '{variant}' ({button_text})")
                break
    
    if styled_count > 0:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        return True
    
    return False

if __name__ == '__main__':
    print("🎨 Applying Premium Button Styling System-Wide...\n")
    
    views_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'ui', 'views')
    
    total_files = 0
    total_styled = 0
    
    for filename in os.listdir(views_dir):
        if filename.endswith('.py') and filename != '__init__.py':
            filepath = os.path.join(views_dir, filename)
            print(f"📄 Processing {filename}...")
            if add_button_styling_to_file(filepath):
                total_files += 1
            print()
    
    print(f"\n✨ Complete! Styled buttons in {total_files} files.")
    print("🚀 Restart the application to see the changes.")
