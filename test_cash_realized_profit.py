#!/usr/bin/env python3
"""
Cash Realized Profit Verification Test

Validates the proportional COGS + payment-based revenue model for credit sales.

Scenario:
  Unit Cost: 115, Unit Price: 160, Quantity: 10
  Total Sale: 1600, Total COGS: 1150, Final Profit: 450

Expected after each payment:
  Payment 1 (600): Revenue=600, COGS=431.25, Profit=168.75
  Payment 2 (500): Revenue=1100, COGS=790.63, Profit=309.38
  Payment 3 (500): Revenue=1600, COGS=1150.00, Profit=450.00
"""

import sqlite3
import os
import sys

# Determine DB path - use the project's pharmacy DB
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'faqiritech_pharmacy.db')

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def cash_realized_profit_query(conn, sale_id):
    """
    Replicates the exact logic from pharmacy_finance_view.py load_summary
    for a single credit sale, returning recognized revenue, COGS, and profit.
    """
    row = conn.execute("""
        SELECT 
            s.total_amount as sale_total,
            COALESCE(
                (SELECT SUM(si.quantity * si.cost_price_at_sale) 
                 FROM pharmacy_sale_items si WHERE si.sale_id = s.id), 0
            ) as sale_cogs,
            COALESCE(
                (SELECT SUM(p.amount) 
                 FROM pharmacy_payments p WHERE p.sale_id = s.id), 0
            ) as collected
        FROM pharmacy_sales s
        WHERE s.id = ?
    """, (sale_id,)).fetchone()
    
    sale_total = row['sale_total']
    sale_cogs = row['sale_cogs']
    collected = min(row['collected'], sale_total)  # Guard: cap at invoice total
    
    if sale_total > 0:
        if collected >= sale_total:
            # Final payment: snap COGS to exact
            recognized_cogs = sale_cogs
        else:
            ratio = collected / sale_total
            recognized_cogs = round(sale_cogs * ratio, 2)
    else:
        recognized_cogs = 0
    
    return {
        'revenue': collected,
        'cogs': recognized_cogs,
        'profit': round(collected - recognized_cogs, 2)
    }

def main():
    print("=" * 60)
    print("CASH REALIZED PROFIT VERIFICATION TEST")
    print("=" * 60)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Use high IDs to avoid collisions with real data
    TEST_SALE_ID = 999999
    TEST_CUSTOMER_ID = 999999
    TEST_LOAN_ID = 999999
    UNIT_COST = 115.0
    UNIT_PRICE = 160.0
    QTY = 10
    SALE_TOTAL = UNIT_PRICE * QTY   # 1600
    SALE_COGS = UNIT_COST * QTY     # 1150
    
    try:
        # ---- SETUP: Clean any previous test data ----
        print("\n[1] Cleaning previous test data...")
        cursor.execute("DELETE FROM pharmacy_payments WHERE sale_id = ?", (TEST_SALE_ID,))
        cursor.execute("DELETE FROM pharmacy_sale_items WHERE sale_id = ?", (TEST_SALE_ID,))
        cursor.execute("DELETE FROM pharmacy_loans WHERE sale_id = ?", (TEST_SALE_ID,))
        cursor.execute("DELETE FROM pharmacy_sales WHERE id = ?", (TEST_SALE_ID,))
        conn.commit()
        print("✅ Clean")
        
        # ---- Create test sale (CREDIT) ----
        print("\n[2] Creating test CREDIT sale...")
        cursor.execute("""
            INSERT INTO pharmacy_sales (id, invoice_number, user_id, customer_id, 
                total_amount, gross_amount, discount_amount, net_amount, payment_type)
            VALUES (?, 'TEST-CRP-001', 1, ?, ?, ?, 0, ?, 'CREDIT')
        """, (TEST_SALE_ID, TEST_CUSTOMER_ID, SALE_TOTAL, SALE_TOTAL, SALE_TOTAL))
        print(f"✅ Sale ID={TEST_SALE_ID}, Total={SALE_TOTAL}, Type=CREDIT")
        
        # ---- Create sale items (10 units @ cost 115, price 160) ----
        print("\n[3] Creating sale items...")
        cursor.execute("""
            INSERT INTO pharmacy_sale_items (sale_id, product_id, quantity, unit_price, 
                total_price, cost_price_at_sale, batch_number)
            VALUES (?, 999, ?, ?, ?, ?, 'TEST-BATCH')
        """, (TEST_SALE_ID, QTY, UNIT_PRICE, SALE_TOTAL, UNIT_COST))
        print(f"✅ {QTY} units @ cost={UNIT_COST}, price={UNIT_PRICE}")
        
        # ---- Create loan record ----
        print("\n[4] Creating loan record...")
        cursor.execute("""
            INSERT INTO pharmacy_loans (id, customer_id, sale_id, loan_amount, 
                total_amount, paid_amount, balance, status)
            VALUES (?, ?, ?, ?, ?, 0, ?, 'PENDING')
        """, (TEST_LOAN_ID, TEST_CUSTOMER_ID, TEST_SALE_ID, SALE_TOTAL, SALE_TOTAL, SALE_TOTAL))
        print(f"✅ Loan ID={TEST_LOAN_ID}, Amount={SALE_TOTAL}")
        conn.commit()
        
        # ---- Before any payment ----
        print("\n[5] Before any payment:")
        result = cash_realized_profit_query(conn, TEST_SALE_ID)
        print(f"   Revenue={result['revenue']}, COGS={result['cogs']}, Profit={result['profit']}")
        assert result['revenue'] == 0, f"Expected revenue=0, got {result['revenue']}"
        assert result['cogs'] == 0, f"Expected COGS=0, got {result['cogs']}"
        print("   ✅ Correct: no revenue or COGS recognized before payments")
        
        # ================================================================
        # PAYMENT 1: 600 AFN
        # ================================================================
        payments = [
            (600, 600.0, 431.25, 168.75),
            (500, 1100.0, 790.63, 309.38),
            (500, 1600.0, 1150.00, 450.00),
        ]
        
        all_passed = True
        for i, (payment_amount, exp_rev, exp_cogs, exp_profit) in enumerate(payments, 1):
            print(f"\n{'='*60}")
            print(f"PAYMENT {i}: {payment_amount} AFN")
            print(f"{'='*60}")
            
            # Insert payment (with sale_id, matching the fix in pharmacy_loan_view.py)
            cursor.execute("""
                INSERT INTO pharmacy_payments (sale_id, loan_id, customer_id, amount, payment_method)
                VALUES (?, ?, ?, ?, 'CASH')
            """, (TEST_SALE_ID, TEST_LOAN_ID, TEST_CUSTOMER_ID, payment_amount))
            conn.commit()
            
            result = cash_realized_profit_query(conn, TEST_SALE_ID)
            
            rev_ok = abs(result['revenue'] - exp_rev) < 0.01
            cogs_ok = abs(result['cogs'] - exp_cogs) < 0.01
            profit_ok = abs(result['profit'] - exp_profit) < 0.01
            
            status_rev = "✅" if rev_ok else "❌"
            status_cogs = "✅" if cogs_ok else "❌"
            status_profit = "✅" if profit_ok else "❌"
            
            print(f"  {status_rev} Revenue: expected={exp_rev}, got={result['revenue']}")
            print(f"  {status_cogs} COGS:    expected={exp_cogs}, got={result['cogs']}")
            print(f"  {status_profit} Profit:  expected={exp_profit}, got={result['profit']}")
            
            if not (rev_ok and cogs_ok and profit_ok):
                all_passed = False
        
        # ---- Final Guards Check ----
        print(f"\n{'='*60}")
        print("GUARD CHECKS")
        print(f"{'='*60}")
        
        # Guard 1: Revenue should never exceed total
        result = cash_realized_profit_query(conn, TEST_SALE_ID)
        guard1 = result['revenue'] <= SALE_TOTAL
        print(f"  {'✅' if guard1 else '❌'} Revenue ({result['revenue']}) ≤ Invoice Total ({SALE_TOTAL})")
        
        # Guard 2: On final payment, COGS must equal full sale_cogs
        guard2 = abs(result['cogs'] - SALE_COGS) < 0.01
        print(f"  {'✅' if guard2 else '❌'} COGS ({result['cogs']}) = Full Sale COGS ({SALE_COGS})")
        
        # Guard 3: Final profit must equal expected
        guard3 = abs(result['profit'] - 450.0) < 0.01
        print(f"  {'✅' if guard3 else '❌'} Profit ({result['profit']}) = Expected Profit (450.00)")
        
        if not (guard1 and guard2 and guard3):
            all_passed = False
        
        # ---- Summary ----
        print(f"\n{'='*60}")
        if all_passed:
            print("🎉 ALL TESTS PASSED — CASH REALIZED PROFIT MODEL VERIFIED!")
        else:
            print("❌ SOME TESTS FAILED")
        print(f"{'='*60}")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED WITH ERROR:")
        print(f"   {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup test data
        print("\n[Cleanup] Removing test data...")
        cursor.execute("DELETE FROM pharmacy_payments WHERE sale_id = ?", (TEST_SALE_ID,))
        cursor.execute("DELETE FROM pharmacy_sale_items WHERE sale_id = ?", (TEST_SALE_ID,))
        cursor.execute("DELETE FROM pharmacy_loans WHERE sale_id = ?", (TEST_SALE_ID,))
        cursor.execute("DELETE FROM pharmacy_sales WHERE id = ?", (TEST_SALE_ID,))
        conn.commit()
        conn.close()
        print("✅ Test data cleaned up")

if __name__ == "__main__":
    main()
