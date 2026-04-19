"""
db_manager.py — Database Layer for Medi-Track Nepal
====================================================
Handles SQLite database initialization, schema creation,
and all CRUD operations for:
  - Products, Stock, Sales, SaleItems, Suppliers

The database file (medi_store.db) is auto-created on first run.
"""

import sqlite3
import os
from datetime import datetime, timedelta

# ---------------------------------------------------------------------------
# Database path — sits alongside the script
# ---------------------------------------------------------------------------
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "medi_store.db")


def get_connection():
    """Return a new SQLite connection with row-factory enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ============================= SCHEMA INIT ==================================

def initialize_database():
    """Create all tables if they don't already exist."""
    conn = get_connection()
    cur = conn.cursor()

    cur.executescript("""
        CREATE TABLE IF NOT EXISTS Products (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            category    TEXT    DEFAULT '',
            hsn_code    TEXT    DEFAULT '',
            min_stock_alert INTEGER DEFAULT 10
        );

        CREATE TABLE IF NOT EXISTS Suppliers (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            name    TEXT    NOT NULL,
            contact TEXT    DEFAULT '',
            address TEXT    DEFAULT '',
            dues    REAL    DEFAULT 0.0
        );

        CREATE TABLE IF NOT EXISTS Stock (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id  INTEGER NOT NULL,
            batch_no    TEXT    DEFAULT '',
            mfg_date    TEXT    DEFAULT '',
            exp_date    TEXT    DEFAULT '',
            qty         INTEGER DEFAULT 0,
            cp          REAL    DEFAULT 0.0,
            mrp         REAL    DEFAULT 0.0,
            sp          REAL    DEFAULT 0.0,
            supplier_id INTEGER DEFAULT NULL,
            FOREIGN KEY (product_id)  REFERENCES Products(id),
            FOREIGN KEY (supplier_id) REFERENCES Suppliers(id)
        );

        CREATE TABLE IF NOT EXISTS Sales (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            bill_no         TEXT    NOT NULL UNIQUE,
            timestamp       TEXT    NOT NULL,
            subtotal        REAL    DEFAULT 0.0,
            discount        REAL    DEFAULT 0.0,
            grand_total     REAL    DEFAULT 0.0,
            payment_type    TEXT    DEFAULT 'Cash',
            customer_name   TEXT    DEFAULT '',
            customer_address TEXT   DEFAULT '',
            customer_pan    TEXT    DEFAULT '',
            customer_phone  TEXT    DEFAULT '',
            customer_dda    TEXT    DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS SaleItems (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_id     INTEGER NOT NULL,
            stock_id    INTEGER NOT NULL,
            qty         INTEGER NOT NULL,
            free_qty    INTEGER DEFAULT 0,
            unit_price  REAL    NOT NULL,
            FOREIGN KEY (sale_id)  REFERENCES Sales(id),
            FOREIGN KEY (stock_id) REFERENCES Stock(id)
        );

        CREATE TABLE IF NOT EXISTS ShopSettings (
            id            INTEGER PRIMARY KEY CHECK (id = 1),
            shop_name     TEXT    DEFAULT 'Kiran Pharmaceuticals Pvt. Ltd.',
            shop_address  TEXT    DEFAULT 'Birgunj, Nepal',
            shop_phone    TEXT    DEFAULT '+977-9824287599/9769333243',
            shop_email    TEXT    DEFAULT 'kiranpharma2080@gmail.com',
            shop_pan      TEXT    DEFAULT '',
            bank_details  TEXT    DEFAULT '',
            logo_path     TEXT    DEFAULT '',
            shop_dda      TEXT    DEFAULT ''
        );
    """)

    # Migration: Add shop_dda to ShopSettings if it doesn't exist
    try:
        conn.execute("ALTER TABLE ShopSettings ADD COLUMN shop_dda TEXT DEFAULT ''")
    except Exception:
        pass  # Column already exists

    # Migration: Add customer_dda to Sales if it doesn't exist
    try:
        conn.execute("ALTER TABLE Sales ADD COLUMN customer_dda TEXT DEFAULT ''")
    except Exception:
        pass  # Column already exists

    conn.commit()
    conn.close()


# ============================= PRODUCTS =====================================

def add_product(name, category="", hsn_code="", min_stock_alert=10):
    """Insert a new product and return its id."""
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO Products (name, category, hsn_code, min_stock_alert) VALUES (?, ?, ?, ?)",
        (name, category, hsn_code, min_stock_alert),
    )
    conn.commit()
    pid = cur.lastrowid
    conn.close()
    return pid


def search_products(query=""):
    """Search products by name (partial match). Returns list of dicts."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM Products WHERE name LIKE ? ORDER BY name",
        (f"%{query}%",),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_products():
    """Return every product."""
    conn = get_connection()
    rows = conn.execute("SELECT * FROM Products ORDER BY name").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_product(product_id, name, category, hsn_code, min_stock_alert):
    """Update an existing product."""
    conn = get_connection()
    conn.execute(
        "UPDATE Products SET name=?, category=?, hsn_code=?, min_stock_alert=? WHERE id=?",
        (name, category, hsn_code, min_stock_alert, product_id),
    )
    conn.commit()
    conn.close()


def delete_product(product_id):
    """Delete a product by id."""
    conn = get_connection()
    conn.execute("DELETE FROM Products WHERE id=?", (product_id,))
    conn.commit()
    conn.close()


# ============================= SUPPLIERS ====================================

def add_supplier(name, contact="", address="", dues=0.0):
    """Insert a new supplier and return its id."""
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO Suppliers (name, contact, address, dues) VALUES (?, ?, ?, ?)",
        (name, contact, address, dues),
    )
    conn.commit()
    sid = cur.lastrowid
    conn.close()
    return sid


def get_all_suppliers():
    """Return every supplier."""
    conn = get_connection()
    rows = conn.execute("SELECT * FROM Suppliers ORDER BY name").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_supplier(supplier_id, name, contact, address, dues):
    """Update an existing supplier."""
    conn = get_connection()
    conn.execute(
        "UPDATE Suppliers SET name=?, contact=?, address=?, dues=? WHERE id=?",
        (name, contact, address, dues, supplier_id),
    )
    conn.commit()
    conn.close()


def delete_supplier(supplier_id):
    """Delete a supplier by id."""
    conn = get_connection()
    conn.execute("DELETE FROM Suppliers WHERE id=?", (supplier_id,))
    conn.commit()
    conn.close()


# ============================= STOCK ========================================

def add_stock(product_id, batch_no, mfg_date, exp_date, qty, cp, mrp, sp, supplier_id=None):
    """Insert a new stock entry and return its id."""
    conn = get_connection()
    cur = conn.execute(
        """INSERT INTO Stock (product_id, batch_no, mfg_date, exp_date, qty, cp, mrp, sp, supplier_id)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (product_id, batch_no, mfg_date, exp_date, qty, cp, mrp, sp, supplier_id),
    )
    conn.commit()
    sid = cur.lastrowid
    conn.close()
    return sid


def get_stock_for_product(product_id):
    """Return all stock rows for a given product."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT s.*, p.name AS product_name
           FROM Stock s JOIN Products p ON s.product_id = p.id
           WHERE s.product_id = ? ORDER BY s.exp_date""",
        (product_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def search_stock(query=""):
    """Search stock by product name or batch number."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT s.*, p.name AS product_name
           FROM Stock s JOIN Products p ON s.product_id = p.id
           WHERE (p.name LIKE ? OR s.batch_no LIKE ?) AND s.qty > 0
           ORDER BY p.name""",
        (f"%{query}%", f"%{query}%"),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def reduce_stock(stock_id, qty):
    """Subtract qty from a stock entry after a sale."""
    conn = get_connection()
    conn.execute("UPDATE Stock SET qty = qty - ? WHERE id = ?", (qty, stock_id))
    conn.commit()
    conn.close()


def get_all_stock():
    """Return every stock entry with product name."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT s.*, p.name AS product_name
           FROM Stock s JOIN Products p ON s.product_id = p.id
           ORDER BY p.name, s.exp_date"""
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ============================= SALES ========================================

def generate_bill_no():
    """Generate a unique bill number like BILL-20260324-001."""
    today = datetime.now().strftime("%Y%m%d")
    conn = get_connection()
    row = conn.execute(
        "SELECT COUNT(*) as cnt FROM Sales WHERE bill_no LIKE ?",
        (f"BILL-{today}-%",),
    ).fetchone()
    conn.close()
    seq = (row["cnt"] if row else 0) + 1
    return f"BILL-{today}-{seq:03d}"


def create_sale(bill_no, subtotal, discount, total, pay_type, items,
                customer_name='', customer_address='', customer_pan='', customer_phone='', customer_dda=''):
    """
    Items: list of dicts with {stock_id, qty, free_qty, unit_price}
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """INSERT INTO Sales (bill_no, timestamp, subtotal, discount, grand_total, payment_type,
                                 customer_name, customer_address, customer_pan, customer_phone, customer_dda)
               VALUES (?, datetime('now', 'localtime'), ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (bill_no, subtotal, discount, total, pay_type, customer_name, customer_address, customer_pan, customer_phone, customer_dda)
        )
        sale_id = cur.lastrowid

        for item in items:
            free_qty = item.get("free_qty", 0)
            conn.execute(
                "INSERT INTO SaleItems (sale_id, stock_id, qty, free_qty, unit_price) VALUES (?, ?, ?, ?, ?)",
                (sale_id, item["stock_id"], item["qty"], free_qty, item["unit_price"]),
            )
            # Auto-subtract stock: paid qty + free qty both leave inventory
            total_out = item["qty"] + free_qty
            conn.execute(
                "UPDATE Stock SET qty = qty - ? WHERE id = ?",
                (total_out, item["stock_id"]),
            )
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()
    return sale_id


def get_sale_with_items(sale_id):
    """Return a sale dict with its items list."""
    conn = get_connection()
    sale = conn.execute("SELECT * FROM Sales WHERE id=?", (sale_id,)).fetchone()
    if not sale:
        conn.close()
        return None
    sale_dict = dict(sale)
    items = conn.execute(
        """SELECT si.*, s.batch_no, s.exp_date, s.mrp, p.name AS product_name, p.category
           FROM SaleItems si
           JOIN Stock s ON si.stock_id = s.id
           JOIN Products p ON s.product_id = p.id
           WHERE si.sale_id = ?""",
        (sale_id,),
    ).fetchall()
    sale_dict["items"] = [dict(i) for i in items]
    conn.close()
    return sale_dict


# ============================= DASHBOARD QUERIES ============================

def get_today_sales_total():
    """Sum of grand_total for today's sales."""
    today = datetime.now().strftime("%Y-%m-%d")
    conn = get_connection()
    row = conn.execute(
        "SELECT COALESCE(SUM(grand_total), 0) AS total FROM Sales WHERE timestamp LIKE ?",
        (f"{today}%",),
    ).fetchone()
    conn.close()
    return row["total"]


def get_today_profit():
    """
    Profit = sum of (unit_price - cp) * qty for today's sale items.
    """
    today = datetime.now().strftime("%Y-%m-%d")
    conn = get_connection()
    row = conn.execute(
        """SELECT COALESCE(SUM((si.unit_price - s.cp) * si.qty), 0) AS profit
           FROM SaleItems si
           JOIN Sales sa ON si.sale_id = sa.id
           JOIN Stock s  ON si.stock_id = s.id
           WHERE sa.timestamp LIKE ?""",
        (f"{today}%",),
    ).fetchone()
    conn.close()
    return row["profit"]


def get_total_items_count():
    """Total distinct products in stock with qty > 0."""
    conn = get_connection()
    row = conn.execute(
        "SELECT COUNT(DISTINCT product_id) AS cnt FROM Stock WHERE qty > 0"
    ).fetchone()
    conn.close()
    return row["cnt"]


def get_expiry_alerts(days=60):
    """Return stock items expiring within `days` days (but not yet expired)."""
    today = datetime.now().strftime("%Y-%m-%d")
    future = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
    conn = get_connection()
    rows = conn.execute(
        """SELECT s.*, p.name AS product_name
           FROM Stock s JOIN Products p ON s.product_id = p.id
           WHERE s.exp_date BETWEEN ? AND ? AND s.qty > 0
           ORDER BY s.exp_date""",
        (today, future),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_expired_items():
    """Return stock items that have already expired."""
    today = datetime.now().strftime("%Y-%m-%d")
    conn = get_connection()
    rows = conn.execute(
        """SELECT s.*, p.name AS product_name
           FROM Stock s JOIN Products p ON s.product_id = p.id
           WHERE s.exp_date < ? AND s.exp_date != '' AND s.qty > 0
           ORDER BY s.exp_date""",
        (today,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_low_stock_items():
    """Return products where total stock qty < min_stock_alert."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT p.id, p.name, p.min_stock_alert,
                  COALESCE(SUM(s.qty), 0) AS total_qty
           FROM Products p
           LEFT JOIN Stock s ON p.id = s.product_id
           GROUP BY p.id
           HAVING total_qty < p.min_stock_alert
           ORDER BY p.name"""
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ============================= REPORT QUERIES ===============================

def get_sales_report(start_date, end_date):
    """
    Return sales within a date range (YYYY-MM-DD format).
    Each row includes bill_no, timestamp, grand_total, payment_type.
    """
    conn = get_connection()
    rows = conn.execute(
        """SELECT * FROM Sales
           WHERE DATE(timestamp) BETWEEN ? AND ?
           ORDER BY timestamp DESC""",
        (start_date, end_date),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_expiry_audit(start_date, end_date):
    """
    Return stock items whose exp_date falls within the given range.
    Useful for identifying items to return to suppliers.
    """
    conn = get_connection()
    rows = conn.execute(
        """SELECT s.*, p.name AS product_name, sup.name AS supplier_name
           FROM Stock s
           JOIN Products  p   ON s.product_id  = p.id
           LEFT JOIN Suppliers sup ON s.supplier_id = sup.id
           WHERE s.exp_date BETWEEN ? AND ? AND s.qty > 0
           ORDER BY s.exp_date""",
        (start_date, end_date),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ============================= SHOP SETTINGS ================================

def get_shop_settings():
    """Return shop settings dict. Creates default row if missing."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM ShopSettings WHERE id = 1").fetchone()
    if not row:
        conn.execute(
            "INSERT INTO ShopSettings (id, shop_name, shop_phone) VALUES (1, 'Kiran Pharmaceuticals Pvt. Ltd.', '+977-9824287599/9769333243')"
        )
        conn.commit()
        row = conn.execute("SELECT * FROM ShopSettings WHERE id = 1").fetchone()
    result = dict(row)
    conn.close()
    return result


def save_shop_settings(shop_name, shop_address, shop_phone, shop_email, shop_pan, bank_details, logo_path, shop_dda):
    """Update settings in id=1 row."""
    conn = get_connection()
    conn.execute(
        """UPDATE ShopSettings
           SET shop_name=?, shop_address=?, shop_phone=?, shop_email=?, shop_pan=?, bank_details=?, logo_path=?, shop_dda=?
           WHERE id = 1""",
        (shop_name, shop_address, shop_phone, shop_email, shop_pan, bank_details, logo_path, shop_dda)
    )
    conn.commit()
    conn.close()
