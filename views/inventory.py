"""
views/inventory.py — Module B: Inventory & Stock-In
=====================================================
Features:
  • Add new products or search existing ones.
  • Stock-in form: Name, Batch No, MFG, EXP, QTY, CP, MRP.
  • Calendar date pickers for MFG and EXP dates.
  • Validation: Expiry Date must be after Manufacturing Date.
  • SP is NOT set here — it's set at POS during sale.
"""

import flet as ft
from datetime import datetime
from db_manager import (
    search_products,
    add_product,
    get_all_products,
    add_stock,
    get_all_stock,
    get_all_suppliers,
)


class InventoryView(ft.Column):
    """Inventory management and stock-in view."""

    def __init__(self, page: ft.Page):
        super().__init__()
        self._page_ref = page
        self.expand = True
        self.scroll = ft.ScrollMode.AUTO
        self.spacing = 20

        # --- Product selection ---
        self.product_search = ft.TextField(
            label="Search or Add Product",
            prefix_icon=ft.Icons.SEARCH,
            hint_text="Type product name…",
            on_change=self._on_product_search,
            border_radius=8,
        )
        self.product_dropdown = ft.Dropdown(
            label="Select Product",
            options=[],
            width=400,
            border_radius=8,
        )
        self.new_product_name = ft.TextField(label="New Product Name", visible=False, border_radius=8)
        self.new_product_category = ft.TextField(label="Category", visible=False, border_radius=8)
        self.new_product_hsn = ft.TextField(label="HSN Code", visible=False, border_radius=8)
        self.new_product_min_stock = ft.TextField(label="Min Stock Alert", value="10", visible=False, border_radius=8, keyboard_type=ft.KeyboardType.NUMBER)
        self.add_product_btn = ft.ElevatedButton(
            "Create New Product", icon=ft.Icons.ADD,
            visible=False, on_click=self._create_product,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
        )
        self.toggle_new_btn = ft.TextButton(
            "➕ New Product", on_click=self._toggle_new_product,
        )

        # --- Stock-in fields ---
        self.batch_no = ft.TextField(label="Batch No", border_radius=8)

        # MFG date with calendar picker
        self.mfg_date_display = ft.TextField(
            label="MFG Date", read_only=True, border_radius=8,
            hint_text="Select date…", expand=True,
        )
        self.mfg_date_picker = ft.DatePicker(
            first_date=datetime(2000, 1, 1),
            last_date=datetime(2050, 12, 31),
            on_change=self._on_mfg_date_picked,
        )
        self.mfg_date_btn = ft.IconButton(
            icon=ft.Icons.CALENDAR_MONTH,
            tooltip="Pick MFG Date",
            on_click=self._open_mfg_picker,
        )

        # EXP date with calendar picker
        self.exp_date_display = ft.TextField(
            label="EXP Date", read_only=True, border_radius=8,
            hint_text="Select date…", expand=True,
        )
        self.exp_date_picker = ft.DatePicker(
            first_date=datetime(2000, 1, 1),
            last_date=datetime(2050, 12, 31),
            on_change=self._on_exp_date_picked,
        )
        self.exp_date_btn = ft.IconButton(
            icon=ft.Icons.CALENDAR_MONTH,
            tooltip="Pick EXP Date",
            on_click=self._open_exp_picker,
        )

        self.qty = ft.TextField(label="Quantity", keyboard_type=ft.KeyboardType.NUMBER, border_radius=8)
        self.cp = ft.TextField(label="Cost Price (CP)", keyboard_type=ft.KeyboardType.NUMBER, border_radius=8)
        self.mrp = ft.TextField(label="MRP", keyboard_type=ft.KeyboardType.NUMBER, border_radius=8)

        self.supplier_dropdown = ft.Dropdown(
            label="Supplier (optional)", options=[], width=400, border_radius=8,
        )

        self.status_text = ft.Text("", size=13)

        self.add_stock_btn = ft.ElevatedButton(
            "Add Stock",
            icon=ft.Icons.ADD_SHOPPING_CART,
            on_click=self._add_stock,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.BLUE_700,
                color=ft.Colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=8),
            ),
        )

        # --- Stock table (no SP column) ---
        self.stock_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Product", weight=ft.FontWeight.W_600, size=12)),
                ft.DataColumn(ft.Text("Batch", weight=ft.FontWeight.W_600, size=12)),
                ft.DataColumn(ft.Text("MFG", weight=ft.FontWeight.W_600, size=12)),
                ft.DataColumn(ft.Text("EXP", weight=ft.FontWeight.W_600, size=12)),
                ft.DataColumn(ft.Text("Qty", weight=ft.FontWeight.W_600, size=12), numeric=True),
                ft.DataColumn(ft.Text("CP", weight=ft.FontWeight.W_600, size=12), numeric=True),
                ft.DataColumn(ft.Text("MRP", weight=ft.FontWeight.W_600, size=12), numeric=True),
            ],
            rows=[],
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=8,
            heading_row_color=ft.Colors.with_opacity(0.05, ft.Colors.BLACK),
            column_spacing=18,
        )

        # Internal state for picked dates (ISO format)
        self._mfg_iso = ""
        self._exp_iso = ""

    def did_mount(self):
        # Register date pickers with the page overlay
        self._page_ref.overlay.append(self.mfg_date_picker)
        self._page_ref.overlay.append(self.exp_date_picker)
        self._page_ref.update()
        self._load_data()

    # ---- Calendar picker handlers ----
    def _open_mfg_picker(self, e):
        self.mfg_date_picker.open = True
        self._page_ref.update()

    def _on_mfg_date_picked(self, e):
        if e.control.value:
            dt = e.control.value
            self._mfg_iso = dt.strftime("%Y-%m-%d")
            self.mfg_date_display.value = dt.strftime("%d/%m/%Y")
            self.mfg_date_display.update()

    def _open_exp_picker(self, e):
        self.exp_date_picker.open = True
        self._page_ref.update()

    def _on_exp_date_picked(self, e):
        if e.control.value:
            dt = e.control.value
            self._exp_iso = dt.strftime("%Y-%m-%d")
            self.exp_date_display.value = dt.strftime("%d/%m/%Y")
            self.exp_date_display.update()

    def _load_data(self):
        """Reload products, suppliers, and stock list."""
        products = get_all_products()
        self.product_dropdown.options = [
            ft.dropdown.Option(key=str(p["id"]), text=p["name"]) for p in products
        ]

        suppliers = get_all_suppliers()
        self.supplier_dropdown.options = [
            ft.dropdown.Option(key=str(s["id"]), text=s["name"]) for s in suppliers
        ]

        stock = get_all_stock()
        self.stock_table.rows = [
            ft.DataRow(cells=[
                ft.DataCell(ft.Text(str(s.get("product_name", "")), size=12)),
                ft.DataCell(ft.Text(str(s.get("batch_no", "")), size=12)),
                ft.DataCell(ft.Text(str(s.get("mfg_date", "")), size=12)),
                ft.DataCell(ft.Text(str(s.get("exp_date", "")), size=12)),
                ft.DataCell(ft.Text(str(s.get("qty", 0)), size=12)),
                ft.DataCell(ft.Text(f"Rs. {s.get('cp', 0):.2f}", size=12)),
                ft.DataCell(ft.Text(f"Rs. {s.get('mrp', 0):.2f}", size=12)),
            ])
            for s in stock
        ]

        self._build_controls()
        self.update()

    def _build_controls(self):
        """Assemble all controls into the view."""
        # Date picker rows with calendar buttons
        mfg_row = ft.Row([self.mfg_date_display, self.mfg_date_btn], spacing=4)
        exp_row = ft.Row([self.exp_date_display, self.exp_date_btn], spacing=4)

        form_card = ft.Container(
            content=ft.Column([
                ft.Text("Add Stock", size=20, weight=ft.FontWeight.BOLD),
                ft.Divider(height=1),
                self.product_search,
                self.product_dropdown,
                ft.Row([self.toggle_new_btn]),
                self.new_product_name,
                ft.Row([self.new_product_category, self.new_product_hsn], spacing=12),
                self.new_product_min_stock,
                self.add_product_btn,
                ft.Divider(height=1),
                ft.Row([self.batch_no, self.qty], spacing=12),
                ft.Row([mfg_row, exp_row], spacing=12),
                ft.Row([self.cp, self.mrp], spacing=12),
                self.supplier_dropdown,
                ft.Row([self.add_stock_btn, self.status_text], spacing=12),
            ], spacing=12),
            padding=24,
            border_radius=12,
            bgcolor=ft.Colors.WHITE,
            shadow=ft.BoxShadow(spread_radius=0, blur_radius=8, color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK), offset=ft.Offset(0, 2)),
        )

        stock_card = ft.Container(
            content=ft.Column([
                ft.Text("Current Stock", size=20, weight=ft.FontWeight.BOLD),
                ft.Divider(height=1),
                self.stock_table,
            ], spacing=8),
            padding=24,
            border_radius=12,
            bgcolor=ft.Colors.WHITE,
            shadow=ft.BoxShadow(spread_radius=0, blur_radius=8, color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK), offset=ft.Offset(0, 2)),
        )

        self.controls = [
            ft.Container(
                content=ft.Column([
                    ft.Text("Inventory & Stock-In", size=28, weight=ft.FontWeight.BOLD),
                    form_card,
                    stock_card,
                ], spacing=20),
                padding=24,
            )
        ]

    def _on_product_search(self, e):
        query = self.product_search.value.strip()
        if not query:
            return
        results = search_products(query)
        self.product_dropdown.options = [
            ft.dropdown.Option(key=str(p["id"]), text=p["name"]) for p in results
        ]
        self.product_dropdown.update()

    def _toggle_new_product(self, e):
        show = not self.new_product_name.visible
        self.new_product_name.visible = show
        self.new_product_category.visible = show
        self.new_product_hsn.visible = show
        self.new_product_min_stock.visible = show
        self.add_product_btn.visible = show
        self.update()

    def _create_product(self, e):
        name = self.new_product_name.value.strip()
        if not name:
            self.status_text.value = "❌ Product name is required."
            self.status_text.color = ft.Colors.RED_700
            self.status_text.update()
            return
        min_s = int(self.new_product_min_stock.value or 10)
        pid = add_product(name, self.new_product_category.value, self.new_product_hsn.value, min_s)
        self.product_dropdown.options.append(ft.dropdown.Option(key=str(pid), text=name))
        self.product_dropdown.value = str(pid)
        self.status_text.value = f"✅ Product '{name}' created."
        self.status_text.color = ft.Colors.GREEN_700
        self._toggle_new_product(None)
        self.update()

    def _add_stock(self, e):
        """Validate inputs and add a stock entry."""
        pid = self.product_dropdown.value
        if not pid:
            self.status_text.value = "❌ Please select a product."
            self.status_text.color = ft.Colors.RED_700
            self.status_text.update()
            return

        # Validate dates
        mfg_iso = self._mfg_iso
        exp_iso = self._exp_iso

        if mfg_iso and exp_iso and exp_iso <= mfg_iso:
            self.status_text.value = "❌ Expiry date must be after manufacturing date."
            self.status_text.color = ft.Colors.RED_700
            self.status_text.update()
            return

        try:
            qty_val = int(self.qty.value or 0)
            cp_val = float(self.cp.value or 0)
            mrp_val = float(self.mrp.value or 0)
        except ValueError:
            self.status_text.value = "❌ Quantity, CP, MRP must be valid numbers."
            self.status_text.color = ft.Colors.RED_700
            self.status_text.update()
            return

        sup_id = int(self.supplier_dropdown.value) if self.supplier_dropdown.value else None

        # SP defaults to 0 — will be set at POS during sale
        add_stock(
            product_id=int(pid),
            batch_no=self.batch_no.value.strip(),
            mfg_date=mfg_iso,
            exp_date=exp_iso,
            qty=qty_val,
            cp=cp_val,
            mrp=mrp_val,
            sp=0.0,
            supplier_id=sup_id,
        )

        self.status_text.value = "✅ Stock added successfully!"
        self.status_text.color = ft.Colors.GREEN_700

        # Clear fields
        for field in [self.batch_no, self.qty, self.cp, self.mrp]:
            field.value = ""
        self.mfg_date_display.value = ""
        self.exp_date_display.value = ""
        self._mfg_iso = ""
        self._exp_iso = ""

        self._load_data()
