#!/usr/bin/env python3
"""
Database Diagnostic Script - Finance Issues
Checks for data integrity problems causing COGS > Revenue
"""

import sqlite3
import os

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), "faqiritech_store.db")

def run_diagnostics():
    print("="*70)
    print("🔍 DATABASE DIAGNOSTICS - Finance Data Integrity Check")
    print("="*70)
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 1. Check Products Table Structure
    print("\n1️⃣  PRODUCTS TABLE - Pricing Check")
    print("-"*70)
    
    cursor.execute("""
        SELECT COUNT(*) as total,
               SUM(CASE WHEN cost_price IS NULL THEN 1 ELSE 0 END) as null_cost,
               SUM(CASE WHEN sale_price IS NULL THEN 1 ELSE 0 END) as null_sale,
               SUM(CASE WHEN cost_price = 0 THEN 1 ELSE 0 END) as zero_cost,
               SUM(CASE WHEN sale_price = 0 THEN 1 ELSE 0 END) as zero_sale,
               SUM(CASE WHEN cost_price > sale_price THEN 1 ELSE 0 END) as loss_makers
        FROM products WHERE is_active = 1
    """)
    
    stats = cursor.fetchone()
    print(f"  Total Active Products: {stats['total']}")
    print(f"  NULL Cost Prices: {stats['null_cost']}")
    print(f"  NULL Sale Prices: {stats['null_sale']}")
    print(f"  Zero Cost Prices: {stats['zero_cost']}")
    print(f"  Zero Sale Prices: {stats['zero_sale']}")
    print(f"  ⚠️  Products with Cost > Sale: {stats['loss_makers']}")
    
    # 2. Products Sold at a Loss
    if stats['loss_makers'] > 0:
        print("\n2️⃣  PRODUCTS SELLING AT A LOSS")
        print("-"*70)
        
        cursor.execute("""
            SELECT id, name_en, barcode, cost_price, sale_price,
                   (cost_price - sale_price) as loss_per_unit
            FROM products 
            WHERE cost_price > sale_price AND is_active = 1
            ORDER BY loss_per_unit DESC
            LIMIT 20
        """)
        
        for row in cursor.fetchall():
            print(f"  ID {row['id']:4d} | {row['name_en'][:30]:30s} | Barcode: {row['barcode']}")
            print(f"           Cost: {row['cost_price']:>10.2f} AFN  |  Sale: {row['sale_price']:>10.2f} AFN  |  Loss: {row['loss_per_unit']:>10.2f} AFN/unit")
            print()
    
    # 3. Sales Summary
    print("\n3️⃣  SALES SUMMARY")
    print("-"*70)
    
    cursor.execute("SELECT COUNT(*) as count, COALESCE(SUM(total_amount), 0) as revenue FROM sales")
    sales = cursor.fetchone()
    print(f"  Total Sales Records: {sales['count']}")
    print(f"  Total Revenue (Sales Table): {sales['revenue']:,.2f} AFN")
    
    # Check for discrepancy between SALES table and SALE_ITEMS table
    cursor.execute("""
        SELECT s.id, s.invoice_number, s.total_amount as sale_total, 
               COALESCE(SUM(si.total_price), 0) as items_total,
               (s.total_amount - COALESCE(SUM(si.total_price), 0)) as diff
        FROM sales s
        LEFT JOIN sale_items si ON s.id = si.sale_id
        GROUP BY s.id
        HAVING ABS(diff) > 1.0
        ORDER BY ABS(diff) DESC
        LIMIT 10
    """)
    discrepancies = cursor.fetchall()
    
    if discrepancies:
        print(f"\n  ⚠️  FOUND {len(discrepancies)} SALES WITH DATA MISMATCH:")
        for d in discrepancies:
            print(f"    Invoice {d['invoice_number']} (ID: {d['id']}):")
            print(f"      Sales Total: {d['sale_total']:,.2f}")
            print(f"      Items Total: {d['items_total']:,.2f}")
            print(f"      Difference:  {d['diff']:,.2f} AFN")
    
    # 4. COGS Breakdown
    print("\n4️⃣  COGS BREAKDOWN")
    print("-"*70)
    
    cursor.execute("""
        SELECT 
            COUNT(*) as items_sold,
            SUM(si.quantity) as total_units,
            SUM(si.quantity * p.cost_price) as total_cogs,
            SUM(si.total_price) as actual_revenue
        FROM sale_items si
        JOIN products p ON si.product_id = p.id
    """)
    
    cogs_data = cursor.fetchone()
    print(f"  Items Sold (line items): {cogs_data['items_sold']}")
    print(f"  Total Units: {cogs_data['total_units']}")
    print(f"  Total COGS: {cogs_data['total_cogs']:,.2f} AFN")
    print(f"  Actual Revenue from Items: {cogs_data['actual_revenue']:,.2f} AFN")
    
    if cogs_data['total_cogs'] > cogs_data['actual_revenue']:
        print(f"  ⚠️  PROBLEM: COGS ({cogs_data['total_cogs']:,.2f}) > Revenue ({cogs_data['actual_revenue']:,.2f})")
        print(f"  Loss Amount: {(cogs_data['total_cogs'] - cogs_data['actual_revenue']):,.2f} AFN")
    
    # 5. Top Loss-Making Sales
    print("\n5️⃣  TOP ITEMS CONTRIBUTING TO LOSS (Cost > Sale Price)")
    print("-"*70)
    
    cursor.execute("""
        SELECT 
            p.id, p.name_en, p.barcode,
            p.cost_price, p.sale_price,
            SUM(si.quantity) as qty_sold,
            SUM(si.quantity * p.cost_price) as total_cost,
            SUM(si.total_price) as total_revenue,
            (SUM(si.quantity * p.cost_price) - SUM(si.total_price)) as total_loss
        FROM sale_items si
        JOIN products p ON si.product_id = p.id
        WHERE p.cost_price > (si.total_price / si.quantity)
        GROUP BY p.id
        ORDER BY total_loss DESC
        LIMIT 10
    """)
    
    loss_items = cursor.fetchall()
    if loss_items:
        for item in loss_items:
            print(f"\n  {item['name_en'][:40]:40s}")
            print(f"    Product ID: {item['id']} | Barcode: {item['barcode']}")
            print(f"    Cost Price: {item['cost_price']:>10.2f} AFN  |  Sale Price: {item['sale_price']:>10.2f} AFN")
            print(f"    Quantity Sold: {item['qty_sold']} units")
            print(f"    Total Cost: {item['total_cost']:>12,.2f} AFN")
            print(f"    Total Revenue: {item['total_revenue']:>12,.2f} AFN")
            print(f"    ❌ LOSS: {item['total_loss']:>12,.2f} AFN")
    else:
        print("  ✅ No items sold at a loss")
    
    # 6. Expenses Check
    print("\n6️⃣  EXPENSES SUMMARY")
    print("-"*70)
    
    cursor.execute("""
        SELECT category, COUNT(*) as count, SUM(amount) as total
        FROM expenses
        GROUP BY category
        ORDER BY total DESC
    """)
    
    for row in cursor.fetchall():
        print(f"  {row['category']:30s}: {row['total']:>12,.2f} AFN ({row['count']} items)")
    
    # 7. Payroll Check
    print("\n7️⃣  PAYROLL SUMMARY")
    print("-"*70)
    
    cursor.execute("""
        SELECT COUNT(*) as count, 
               SUM(base_salary) as total_base,
               SUM(deductions) as total_deductions,
               SUM(net_paid) as total_paid
        FROM payroll
    """)
    
    payroll = cursor.fetchone()
    print(f"  Payroll Entries: {payroll['count']}")
    print(f"  Total Base Salary: {payroll['total_base'] or 0:,.2f} AFN")
    print(f"  Total Deductions: {payroll['total_deductions'] or 0:,.2f} AFN")
    print(f"  Total Net Paid: {payroll['total_paid'] or 0:,.2f} AFN")
    
    # 8. Final Calculation
    print("\n8️⃣  CALCULATED NET PROFIT")
    print("="*70)
    
    gross = sales['revenue']
    cogs = cogs_data['total_cogs']
    
    cursor.execute("""
        SELECT COALESCE(SUM(amount), 0) as total
        FROM expenses 
        WHERE category NOT IN ('Salary', 'Advance Salary', 'Payroll')
    """)
    expenses = cursor.fetchone()['total']
    
    salaries = payroll['total_paid'] or 0
    profit = gross - cogs - expenses - salaries
    
    print(f"  Gross Sales:     {gross:>15,.2f} AFN")
    print(f"  COGS:           -{cogs:>15,.2f} AFN")
    print(f"  Expenses:       -{expenses:>15,.2f} AFN")
    print(f"  Salaries:       -{salaries:>15,.2f} AFN")
    print(f"  {'-'*50}")
    print(f"  Net Profit:      {profit:>15,.2f} AFN")
    
    if profit < 0:
        print(f"\n  ⚠️  NEGATIVE PROFIT!")
        print(f"  Main Issue: {'COGS > Revenue' if cogs > gross else 'High Expenses'}")
    
    print("="*70)
    
    conn.close()

if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found at: {DB_PATH}")
        print("Please run this script from the project root directory.")
    else:
        run_diagnostics()
