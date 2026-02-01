"""
Auto-apply premium table styling to all views
Run this once to upgrade all tables system-wide
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def add_table_styling_to_file(filepath, table_var_name, variant="premium"):
    """Add styling import and application to a Python file"""
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if already styled
    if 'from src.ui.table_styles import style_table' in content:
        print(f"✓ {filepath} already has table styling")
        return False
    
    # Add import at top (after other imports)
    import_line = "from src.ui.table_styles import style_table\n"
    
    # Find last import
    lines = content.split('\n')
    last_import_idx = 0
    for i, line in enumerate(lines):
        if line.startswith('import ') or line.startswith('from '):
            last_import_idx = i
    
    # Insert import
    lines.insert(last_import_idx + 1, import_line.strip())
    
    # Find table initialization and add styling right after
    for i, line in enumerate(lines):
        if f'{table_var_name} = QTableWidget(' in line:
            # Find the end of table setup (usually after setHorizontalHeaderLabels or similar)
            insert_idx = i + 1
            
            # Skip to after header setup
            for j in range(i+1, min(i+10, len(lines))):
                if 'setHorizontalHeaderLabels' in lines[j]:
                    insert_idx = j + 1
                    break
            
            # Insert styling call
            indent = len(line) - len(line.lstrip())
            style_line = ' ' * indent + f'style_table({table_var_name}, variant="{variant}")'
            lines.insert(insert_idx, style_line)
            break
    
    # Write back
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print(f"✅ Styled {table_var_name} in {filepath}")
    return True

# Table mapping: (file, table_variable, variant)
tables_to_style = [
    ('src/ui/views/inventory_view.py', 'self.table', 'premium'),
    ('src/ui/views/customer_view.py', 'self.table', 'premium'),
    ('src/ui/views/supplier_view.py', 'self.table', 'premium'),
    ('src/ui/views/loan_view.py', 'self.table', 'premium'),
    ('src/ui/views/stock_alert_view.py', 'self.table', 'compact'),
    ('src/ui/views/reports_view.py', 'self.low_stock_table', 'compact'),
    ('src/ui/views/reports_view.py', 'self.sales_table', 'premium'),
    ('src/ui/views/reports_view.py', 'self.product_table', 'premium'),
    ('src/ui/views/reports_view.py', 'self.returns_table', 'premium'),
    ('src/ui/views/sales_view.py', 'self.results_table', 'premium'),
    ('src/ui/views/super_admin_view.py', 'self.user_table', 'premium'),
]

if __name__ == '__main__':
    print("🎨 Applying Premium Table Styling System-Wide...\n")
    
    styled_count = 0
    for filepath, table_var, variant in tables_to_style:
        full_path = os.path.join(os.path.dirname(__file__), '..', '..', filepath)
        if os.path.exists(full_path):
            if add_table_styling_to_file(full_path, table_var, variant):
                styled_count += 1
        else:
            print(f"⚠️  File not found: {full_path}")
    
    print(f"\n✨ Complete! Styled {styled_count} tables across the system.")
    print("🚀 Restart the application to see the changes.")
