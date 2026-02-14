#!/usr/bin/env python3
"""
Enterprise Batch Tracking Verification Test
Tests FEFO with multi-batch allocation and weighted average cost calculation
"""

import sqlite3
import sys
sys.path.insert(0, 'src')

from database.db_manager import DatabaseManager
from core.ledger_manager import ledger_manager

def main():
    print("="*60)
    print("ENTERPRISE BATCH TRACKING VERIFICATION TEST")
    print("="*60)
    
    # Initialize database
    print("\n[1] Initializing database...")
    db = DatabaseManager()
    # The database is initialized automatically when DatabaseManager is created
    
    conn = sqlite3.connect('faqiritech_pharmacy.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        # Verify tables exist
        print("\n[2] Verifying tables...")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pharmacy_batches'")
        if not cursor.fetchone():
            print("❌ pharmacy_batches table not found!")
            return
        print("✅ pharmacy_batches table exists")
        
        # Create test product
        print("\n[3] Creating test product...")
        cursor.execute("DELETE FROM pharmacy_products WHERE id = 999")
        cursor.execute("""
            INSERT INTO pharmacy_products (id, barcode, name_en, cost_price, sale_price, pack_size) 
            VALUES (999, 'TEST999', 'TEST_FEFO_PRODUCT', 90, 150, 1)
        """)
        conn.commit()
        print("✅ Test product created (ID: 999)")
        
        # Create Batch A (cost=80, expires 2026-03-01)
        print("\n[4] Creating Batch A...")
        cursor.execute("DELETE FROM pharmacy_batches WHERE product_id = 999")
        cursor.execute("""
            INSERT INTO pharmacy_batches 
            (product_id, batch_number, expiry_date, purchase_cost_per_unit, qty_received, qty_remaining)
            VALUES (999, 'BATCH_A', '2026-03-01', 80, 50, 50)
        """)
        print("✅ Batch A: qty=50, cost=80, expiry=2026-03-01")
        
        # Create Batch B (cost=100, expires 2026-06-01)
        print("\n[5] Creating Batch B...")
        cursor.execute("""
            INSERT INTO pharmacy_batches 
            (product_id, batch_number, expiry_date, purchase_cost_per_unit, qty_received, qty_remaining)
            VALUES (999, 'BATCH_B', '2026-06-01', 100, 50, 50)
        """)
        conn.commit()
        print("✅ Batch B: qty=50, cost=100, expiry=2026-06-01")
        
        # Test FEFO sale of 75 units
        print("\n[6] Testing FEFO sale of 75 units...")
        allocations = ledger_manager.record_pharmacy_sale(
            conn, 
            product_id=999, 
            sale_id=99999, 
            sale_item_id=99999,
            quantity=75, 
            details='FEFO Verification Test'
        )
        
        print(f"\n{'='*60}")
        print("ALLOCATION RESULTS")
        print(f"{'='*60}")
        for i, alloc in enumerate(allocations, 1):
            print(f"Allocation {i}:")
            print(f"  Batch: {alloc['batch_number']}")
            print(f"  Qty: {alloc['qty']}")
            print(f"  Cost: {alloc['cost']}")
            print(f"  Expiry: {alloc['expiry']}")
        
        # Calculate weighted average cost
        total_cost = sum(a['qty'] * a['cost'] for a in allocations)
        total_qty = sum(a['qty'] for a in allocations)
        weighted_avg = total_cost / total_qty
        
        print(f"\n{'='*60}")
        print("WEIGHTED AVERAGE COST CALCULATION")
        print(f"{'='*60}")
        print(f"Total Cost: {total_cost} = (50×80) + (25×100)")
        print(f"Total Qty: {total_qty}")
        print(f"Weighted Avg: {weighted_avg:.2f}")
        print(f"Expected: 86.67")
        
        # Verify ledger entries
        print(f"\n{'='*60}")
        print("LEDGER VERIFICATION")
        print(f"{'='*60}")
        cursor.execute("""
            SELECT type, quantity, cost_price, batch_number, details
            FROM pharmacy_stock_ledger
            WHERE product_id = 999 AND type = 'SALE'
            ORDER BY id
        """)
        ledger_entries = cursor.fetchall()
        print(f"Ledger entries: {len(ledger_entries)}")
        for i, entry in enumerate(ledger_entries, 1):
            print(f"  Entry {i}: {entry['batch_number']}, qty={entry['quantity']}, cost={entry['cost_price']}")
        
        # Verify allocation table
        print(f"\n{'='*60}")
        print("ALLOCATION TABLE VERIFICATION")
        print(f"{'='*60}")
        cursor.execute("""
            SELECT a.qty_allocated, a.unit_cost, b.batch_number
            FROM pharmacy_sale_batch_allocations a
            JOIN pharmacy_batches b ON a.batch_id = b.batch_id
            WHERE a.sale_item_id = 99999
            ORDER BY a.allocation_id
        """)
        alloc_records = cursor.fetchall()
        print(f"Allocation records: {len(alloc_records)}")
        for i, rec in enumerate(alloc_records, 1):
            print(f"  Record {i}: {rec['batch_number']}, qty={rec['qty_allocated']}, cost={rec['unit_cost']}")
        
        # Verify remaining quantities
        print(f"\n{'='*60}")
        print("REMAINING STOCK VERIFICATION")
        print(f"{'='*60}")
        cursor.execute("""
            SELECT batch_number, qty_remaining
            FROM pharmacy_batches
            WHERE product_id = 999
            ORDER BY expiry_date
        """)
        remaining = cursor.fetchall()
        for batch in remaining:
            print(f"  {batch['batch_number']}: {batch['qty_remaining']} units remaining")
        
        conn.commit()
        
        # Final verification
        print(f"\n{'='*60}")
        print("TEST RESULTS")
        print(f"{'='*60}")
        
        checks = []
        checks.append(("Ledger has 2 SALE entries", len(ledger_entries) == 2))
        checks.append(("Allocation table shows correct split", len(alloc_records) == 2))
        checks.append(("Weighted avg cost = 86.67", abs(weighted_avg - 86.67) < 0.01))
        checks.append(("Batch A fully consumed", remaining[0]['qty_remaining'] == 0))
        checks.append(("Batch B has 25 remaining", remaining[1]['qty_remaining'] == 25))
        
        all_passed = all(check[1] for check in checks)
        
        for check_name, passed in checks:
            status = "✅" if passed else "❌"
            print(f"{status} {check_name}")
        
        if all_passed:
            print(f"\n{'='*60}")
            print("🎉 ALL TESTS PASSED - ENTERPRISE BATCH TRACKING VERIFIED!")
            print(f"{'='*60}")
        else:
            print(f"\n{'='*60}")
            print("❌ SOME TESTS FAILED")
            print(f"{'='*60}")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED WITH ERROR:")
        print(f"{type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    main()
