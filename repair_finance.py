#!/usr/bin/env python3
"""
Database Repair Script - Fix Sales Total Discrepancies
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "faqiritech_store.db")

def repair_database():
    print("="*70)
    print("🛠️  DATABASE REPAIR - Fixing Sales Totals & Orphans")
    print("="*70)
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found at: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        # 1. FIXED: Update Sales Total from Sale Items
        print("\n1️⃣  RECALCULATING SALES TOTALS...")
        
        # Find mismatched sales
        cursor.execute("""
            SELECT s.id, s.invoice_number, s.total_amount as old_total, 
                   COALESCE(SUM(si.total_price), 0) as new_total
            FROM sales s
            LEFT JOIN sale_items si ON s.id = si.sale_id
            GROUP BY s.id
            HAVING ABS(s.total_amount - COALESCE(SUM(si.total_price), 0)) > 1.0
        """)
        mismatches = cursor.fetchall()
        
        if not mismatches:
            print("  ✅ All sales totals match their items.")
        else:
            print(f"  ⚠️  Found {len(mismatches)} sales to fix:")
            for m in mismatches:
                diff = m['new_total'] - m['old_total']
                print(f"    - Sale ID {m['id']} ({m['invoice_number']}): {m['old_total']:,.2f} -> {m['new_total']:,.2f} (Diff: {diff:+,.2f})")
                
                # UPDATE sales total
                cursor.execute("UPDATE sales SET total_amount = ? WHERE id = ?", (m['new_total'], m['id']))
            
            conn.commit()
            print(f"  ✅ Corrected {len(mismatches)} sales records.")

        # 2. DELETE ORPHANED SALES (0 items but > 0 total)
        # Note: If new_total was 0, the previous step updated sales.total_amount to 0.
        # Now we can delete empty sales created by failed transactions.
        
        print("\n2️⃣  CLEANING UP EMPTY/FAILED SALES...")
        
        cursor.execute("SELECT COUNT(*) FROM sales WHERE total_amount = 0")
        empty_count = cursor.fetchone()[0]
        
        if empty_count > 0:
            cursor.execute("DELETE FROM sales WHERE total_amount = 0")
            conn.commit()
            print(f"  ✅ Deleted {empty_count} empty/failed sales records.")
        else:
            print("  ✅ No empty sales found.")

        # 3. VERIFY RESULT
        print("\n3️⃣  VERIFICATION...")
        cursor.execute("SELECT COALESCE(SUM(total_amount), 0) FROM sales")
        new_revenue = cursor.fetchone()[0]
        print(f"  New Total Revenue: {new_revenue:,.2f} AFN")
        
    except Exception as e:
        print(f"❌ Error during repair: {e}")
        conn.rollback()
    finally:
        conn.close()
        print("\n✨ Database repair complete.")

if __name__ == "__main__":
    repair_database()
