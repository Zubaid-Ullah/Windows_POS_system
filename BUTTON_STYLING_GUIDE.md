# Button Styling Guide

## 🎨 Premium Button System

Your POS system now has a comprehensive, professional button styling system with semantic colors and consistent design.

### Color Variants

#### 🔵 Primary (Blue) - Main Actions
- **Use for**: Update, Edit, Modify, Refresh, Print, Export
- **Color**: `#2196f3`
- **Example**: Refresh List, Update Product, Export Data

#### 🟢 Success (Green) - Positive Actions
- **Use for**: Add, Create, Save, Submit, Confirm, Complete
- **Color**: `#4caf50`
- **Example**: Add Customer, Save Changes, Complete Sale

#### 🔴 Danger (Red) - Destructive Actions
- **Use for**: Delete, Remove, Cancel Order, Clear All
- **Color**: `#f44336`
- **Example**: Delete Item, Remove Customer, Clear Cart

#### 🟠 Warning (Orange) - Caution
- **Use for**: Reset, Clear, Undo, Restore
- **Color**: `#ff9800`
- **Example**: Reset Form, Clear Filters

#### ⚫ Secondary (Gray) - Less Important
- **Use for**: Close, Back, Cancel (non-destructive)
- **Color**: `#607d8b`
- **Example**: Close Dialog, Go Back

#### 🔷 Info (Cyan) - Informational
- **Use for**: View, Details, Info, Search
- **Color**: `#00bcd4`
- **Example**: View Details, Show Info, Credit Payment

### Size Variants

#### Normal (Default)
- Height: 36px
- Padding: 10px 20px
- Font: 14px, weight 600
- **Use for**: Most buttons

#### Large
- Height: 50px
- Padding: 16px 32px
- Font: 16px, weight 700
- **Use for**: Critical actions (Payment buttons, Submit forms)

#### Icon
- Size: 32x32px
- Padding: 6px 10px
- Font: 12px
- **Use for**: Table action buttons, toolbar icons

### Style Variants

#### Filled (Default)
Solid background color with white text.

#### Outline
Transparent background with colored border and text. Fills with color on hover.

---

## 📝 Usage Examples

### Python Code

```python
from src.ui.button_styles import style_button

# Success button (green)
add_btn = QPushButton("Add Customer")
style_button(add_btn, variant="success")

# Danger button (red)
delete_btn = QPushButton("Delete")
style_button(delete_btn, variant="danger")

# Large primary button
submit_btn = QPushButton("Complete Payment")
style_button(submit_btn, variant="primary", size="large")

# Icon button for table
edit_btn = QPushButton()
edit_btn.setIcon(qta.icon("fa5s.edit", color="white"))
style_button(edit_btn, variant="info", size="icon")

# Outline button
cancel_btn = QPushButton("Cancel")
style_button(cancel_btn, variant="outline")
```

---

## ✅ Applied Throughout System

The button styling has been automatically applied to:

### Sales View
- ✅ Cash Payment (Large Green)
- ✅ Credit Payment (Large Cyan)
- ✅ Clear Cart (Large Red)
- ✅ Search Button (Blue Icon)
- ✅ Stock Check (Orange Icon)
- ✅ Delete from Cart (Red Icon)
- ✅ Return Items (Blue)

### Customer View
- ✅ Add Customer (Green)

### Supplier View
- ✅ Add Supplier (Green)

### Inventory View
- ✅ Add Product (Green)
- ✅ Categories (Blue)

### Reports View
- ✅ Export Data (Blue)

### Super Admin View
- ✅ System Toggle (Blue)

---

## 🎯 Design Principles

1. **Semantic Colors**: Colors match action meaning (green=add, red=delete)
2. **Visual Hierarchy**: Size indicates importance
3. **Consistency**: Same actions look the same everywhere
4. **Accessibility**: High contrast, clear hover states
5. **Touch-Friendly**: Minimum 36px height, larger for critical actions

---

## 🚀 Benefits

- **Professional Appearance**: Modern, polished UI
- **Better UX**: Users instantly understand button purpose
- **Reduced Errors**: Destructive actions clearly marked in red
- **Faster Learning**: Consistent patterns across all views
- **Maintainability**: Centralized styling, easy to update
