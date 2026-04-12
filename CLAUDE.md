# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Medi-Track Nepal** is a medical store ERP (Enterprise Resource Planning) desktop application built with Python and Flet. It manages inventory, sales (POS), suppliers, and generates reports for a medical/pharmacy business. The app is packaged as a standalone executable using PyInstaller.

## Development Commands

### Running the Application

**macOS/Linux:**
```bash
chmod +x run.sh && ./run.sh
```

**Windows:**
```bash
run.bat
```

### Build Executable

**Windows (.exe):**
```bash
build_exe.bat
```
Output: `dist/MediTrackNepal/MediTrackNepal.exe`

**macOS (.app):**
```bash
# First install pyinstaller in venv
source .venv/bin/activate
pip install pyinstaller

# Build
pyinstaller MediTrackNepal.spec
```
Output: `dist/MediTrackNepal.app`

### Manual Setup

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the app
python main.py
```

## Architecture

### Technology Stack

- **UI Framework:** [Flet](https://flet.dev) (Material 3 design, desktop mode)
- **Database:** SQLite (`medi_store.db`)
- **Packaging:** PyInstaller (cross-platform executables)

### File Structure

```
pms/
├── main.py                    # Application entry point, NavigationRail setup
├── db_manager.py              # All database CRUD operations (SQLite)
├── requirements.txt           # Python dependencies (flet)
├── MediTrackNepal.spec        # PyInstaller configuration
├── run.sh / run.bat           # Launch scripts
├── build_exe.bat              # Windows executable builder
├── medi_store.db              # SQLite database (auto-created)
└── views/                     # UI view modules (Flet controls)
    ├── __init__.py
    ├── dashboard.py           # Dashboard with sales/profit stats, expiry alerts
    ├── inventory.py           # Products and stock management
    ├── pos.py                 # Point of Sale (billing)
    ├── reports.py             # Sales reports and expiry audit
    ├── suppliers.py           # Supplier management
    └── settings.py            # Shop settings (name, logo)
```

### Database Schema

**Tables:**
- `Products` — Product catalog (name, category, HSN code, min stock alert)
- `Stock` — Inventory batches with expiry dates (qty, cost price, MRP, sale price)
- `Suppliers` — Supplier contact info and dues
- `Sales` — Sale transactions (bill_no, timestamp, totals, payment type)
- `SaleItems` — Line items per sale
- `ShopSettings` — Shop configuration (single row, id=1)

**Key Relationships:**
- Stock has foreign keys to Products and Suppliers
- SaleItems links Sales to Stock

### View Architecture

Each view module exposes a class extending `ft.Column` (Flet container):

- `DashboardView(page)` — Auto-refreshes on navigation, shows alerts
- `InventoryView(page)` — Product/stock CRUD with dialogs
- `POSView(page)` — Cart-based billing with real-time totals
- `ReportsView(page)` — Date range reports for sales/expiry
- `SuppliersView(page)` — Supplier CRUD with dues tracking
- `SettingsView(page)` — Shop name/logo configuration

Views are lazily instantiated in `main.py:get_view()` and cached.

### Key Implementation Details

**Database Access:** All DB operations are in `db_manager.py`. Uses `sqlite3.Row` factory for dict-like rows. Always calls `PRAGMA foreign_keys = ON`.

**Bill Number Generation:** Format `BILL-YYYYMMDD-XXX` (auto-increments per day) via `generate_bill_no()`.

**Expiry Alerts:**
- Expiring soon: < 60 days (orange)
- Already expired (red)
- Low stock: qty < min_stock_alert (amber)

**Stock Reduction:** Automatically decrements stock qty when creating a sale via `create_sale()`.

**Data Flow:** Views call `db_manager` functions directly (synchronous). No ORM or async patterns.

## Common Tasks

### Adding a New Field to Products

1. Update `initialize_database()` in `db_manager.py` — add column to `CREATE TABLE`
2. Add CRUD function (e.g., `update_product_field()`)
3. Update `InventoryView` UI to display/edit the field

### Adding a New View Tab

1. Create module in `views/newtab.py` with class extending `ft.Column`
2. Add `NavigationRailDestination` in `main.py`
3. Add case in `get_view()` switch statement
4. Add to `hiddenimports` in `MediTrackNepal.spec`

### Debugging Database Issues

The database is `medi_store.db` in the project root. Inspect with:
```bash
sqlite3 medi_store.db ".schema"
sqlite3 medi_store.db "SELECT * FROM Products LIMIT 5;"
```

### Rebuild After Adding Dependencies

Update `requirements.txt`, then update `run.sh`/`run.bat` to check for the new package, and add hidden imports to `MediTrackNepal.spec` if needed.
