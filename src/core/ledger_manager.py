import os
from datetime import datetime
from src.database.db_manager import db_manager

class LedgerManager:
    """Handles inventory ledger entries and cost calculations."""
    
    # --- STORE LOGIC (Weighted Average Cost) ---
    @staticmethod
    def record_store_movement(conn, product_id, mtype, qty, reference_id, details=""):
        """Records a movement in the Store stock_ledger and updates inventory."""
        cursor = conn.cursor()
        
        # 1. Get current cost from products
        cursor.execute("SELECT cost_price FROM products WHERE id = ?", (product_id,))
        prod = cursor.fetchone()
        cost_at_sale = prod['cost_price'] if prod else 0
        
        # 2. Record in ledger
        cursor.execute("""
            INSERT INTO stock_ledger (product_id, type, quantity, cost_price, reference_id, details)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (product_id, mtype, qty, cost_at_sale, reference_id, details))
        
        # 3. Update inventory
        # For SALE, qty should be negative in the call or we handle it here
        # Let's assume qty passed is absolute and we subtract for SALES/RETURNS
        if mtype == 'SALE':
            cursor.execute("UPDATE inventory SET quantity = quantity - ? WHERE product_id = ?", (qty, product_id))
        elif mtype == 'PURCHASE' or mtype == 'ADJUSTMENT' or mtype == 'RETURN':
            # For PURCHASE/ADJUSTMENT, qty is positive addition
            cursor.execute("UPDATE inventory SET quantity = quantity + ? WHERE product_id = ?", (qty, product_id))
            
            # Update WAC if it's a PURCHASE? 
            # In a true WAC, we'd update products.cost_price here:
            # new_cost = (old_qty * old_cost + new_qty * new_cost) / (old_qty + new_qty)
            # For now, we assume the user updates the product cost price when adding stock.

    @staticmethod
    def get_store_wac(conn, product_id):
        """Returns the current cost_price (WAC) for a Store product."""
        cursor = conn.cursor()
        cursor.execute("SELECT cost_price FROM products WHERE id = ?", (product_id,))
        res = cursor.fetchone()
        return res['cost_price'] if res else 0

    # --- PHARMACY LOGIC (FEFO - First Expiry First Out) ---
    @staticmethod
    def record_pharmacy_sale(conn, product_id, sale_id, sale_item_id, quantity, details="", unit_type="Pack", pack_size=1):
        """
        ENTERPRISE FEFO SALE PROCESSING WITH PACK/UNIT COST CONVERSION
        
        Processes a pharmacy sale using FEFO (First-Expiry-First-Out).
        - Queries pharmacy_batches ordered by expiry_date
        - Uses exact batch purchase_cost_per_unit (NO FALLBACK)
        - **CRITICAL**: Converts pack-level cost to unit-level cost when needed
        - Supports multi-batch splitting
        - Creates allocation records for traceability
        - Writes one ledger entry per batch consumed
        - Validates cost > 0 (raises error if invalid)
        
        Args:
            conn: Database connection
            product_id: Product ID
            sale_id: Sale ID
            sale_item_id: Sale item ID for allocation tracking
            quantity: Quantity to sell (in base units)
            details: Transaction details
            unit_type: "Pack" or "Unit" - how the sale was made
            pack_size: Number of units per pack (for cost conversion)
        
        Returns:
            list: Allocation details [{batch_id, batch_number, expiry, qty, cost}, ...]
        
        Raises:
            ValueError: If insufficient stock or invalid batch cost
        """
        cursor = conn.cursor()
        
        # 1. Fetch available batches ordered by FEFO (expiry_date ASC)
        cursor.execute("""
            SELECT batch_id, batch_number, expiry_date, qty_remaining, purchase_cost_per_unit
            FROM pharmacy_batches
            WHERE product_id = ? AND qty_remaining > 0
            ORDER BY expiry_date ASC, batch_id ASC
        """, (product_id,))
        batches = cursor.fetchall()
        
        if not batches:
            raise ValueError(f"No stock available for product_id {product_id}")
        
        remaining_to_sell = quantity
        allocations = []
        
        for batch in batches:
            if remaining_to_sell <= 0:
                break
            
            batch_id = batch['batch_id']
            batch_number = batch['batch_number']
            expiry_date = batch['expiry_date']
            qty_available = batch['qty_remaining']
            batch_cost = batch['purchase_cost_per_unit']
            
            # CRITICAL: Validate cost - NEVER allow missing or zero cost
            if batch_cost is None or batch_cost <= 0:
                raise ValueError(
                    f"CRITICAL: Batch {batch_id} (batch_number: {batch_number}) has invalid cost ({batch_cost}). "
                    f"Sale cannot proceed. Please fix batch cost in inventory management."
                )
            
            # CRITICAL FIX: Pack/Unit Cost Conversion
            # Batch cost is ALWAYS stored per pack
            # If selling by Unit, we must convert: unit_cost = pack_cost / pack_size
            unit_cost = batch_cost
            if unit_type == "Unit" and pack_size > 1:
                unit_cost = batch_cost / pack_size
            
            # Calculate quantity to take from this batch
            qty_to_take = min(remaining_to_sell, qty_available)
            
            # Write ledger entry (one per batch consumed)
            # Use CONVERTED unit_cost for accurate COGS
            cursor.execute("""
                INSERT INTO pharmacy_stock_ledger 
                (product_id, type, quantity, cost_price, batch_number, reference_id, details)
                VALUES (?, 'SALE', ?, ?, ?, ?, ?)
            """, (product_id, qty_to_take, unit_cost, batch_number, sale_id, 
                  f"Sale item {sale_item_id} - {details} ({unit_type})"))
            
            # Update batch quantity (deduct stock)
            new_remaining = qty_available - qty_to_take
            if new_remaining < 0:
                raise ValueError(f"CRITICAL: Negative stock detected for batch {batch_id}")
            
            cursor.execute("""
                UPDATE pharmacy_batches 
                SET qty_remaining = ?
                WHERE batch_id = ?
            """, (new_remaining, batch_id))
            
            # Record allocation for exact traceability
            # Use CONVERTED unit_cost
            cursor.execute("""
                INSERT INTO pharmacy_sale_batch_allocations 
                (sale_item_id, batch_id, qty_allocated, unit_cost)
                VALUES (?, ?, ?, ?)
            """, (sale_item_id, batch_id, qty_to_take, unit_cost))
            
            # Track allocation details for return
            allocations.append({
                'batch_id': batch_id,
                'batch_number': batch_number,
                'expiry': expiry_date,
                'qty': qty_to_take,
                'cost': unit_cost  # Return CONVERTED cost
            })
            
            remaining_to_sell -= qty_to_take
        
        # Check if we fulfilled the entire quantity
        if remaining_to_sell > 0:
            raise ValueError(
                f"Insufficient stock for product_id {product_id}. "
                f"Requested: {quantity}, Available: {quantity - remaining_to_sell}, "
                f"Short: {remaining_to_sell} units"
            )
        
        return allocations

    @staticmethod
    def record_pharmacy_movement(conn, product_id, mtype, qty, batch_number, reference_id, details=""):
        """Records general pharmacy movement (Purchase/Adjustment)."""
        cursor = conn.cursor()
        
        cursor.execute("SELECT cost_price FROM pharmacy_products WHERE id = ?", (product_id,))
        prod = cursor.fetchone()
        cost = prod['cost_price'] if prod else 0
        
        cursor.execute("""
            INSERT INTO pharmacy_stock_ledger (product_id, type, quantity, cost_price, batch_number, reference_id, details)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (product_id, mtype, qty, cost, batch_number, reference_id, details))
        
        if mtype in ['PURCHASE', 'ADJUSTMENT', 'RETURN']:
            cursor.execute("""
                UPDATE pharmacy_inventory SET quantity = quantity + ? 
                WHERE product_id = ? AND batch_number = ?
            """, (qty, product_id, batch_number))
            # If batch doesn't exist? (Should be handled by inventory logic)

ledger_manager = LedgerManager()
