"""
views/pos.py — Module C: Point of Sale (POS)
==============================================
Features:
  • Instant search bar for products (by name or batch).
  • Cart system with editable selling price (SP set at sale time).
  • Payment options: Cash, Credit, Online.
  • Complete Sale: auto-subtracts stock, generates bill number.
  • Print-ready bill with shop name & logo (HTML for printing).
"""

import flet as ft
import os
import base64
import tempfile
import webbrowser
from datetime import datetime
from db_manager import (
    search_stock,
    generate_bill_no,
    create_sale,
    get_sale_with_items,
    get_shop_settings,
)


class POSView(ft.Column):
    """Point-of-sale view with search, cart, and billing."""

    def __init__(self, page: ft.Page):
        super().__init__()
        self._page_ref = page
        self.expand = True
        self.scroll = ft.ScrollMode.AUTO
        self.spacing = 20

        # Internal cart: list of dicts {stock_id, product_name, batch_no, qty, unit_price, max_qty, mrp}
        self.cart: list[dict] = []

        # --- Search ---
        self.search_field = ft.TextField(
            label="Search Product (Name or Batch)",
            prefix_icon=ft.Icons.SEARCH,
            on_submit=self._do_search,
            on_change=self._do_search,
            border_radius=8,
            expand=True,
        )

        # --- Search results list ---
        self.search_results = ft.Column(spacing=4)

        # --- Cart table ---
        self.cart_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Product", weight=ft.FontWeight.W_600, size=12)),
                ft.DataColumn(ft.Text("Batch", weight=ft.FontWeight.W_600, size=12)),
                ft.DataColumn(ft.Text("MRP", weight=ft.FontWeight.W_600, size=12), numeric=True),
                ft.DataColumn(ft.Text("Sell Price", weight=ft.FontWeight.W_600, size=12), numeric=True),
                ft.DataColumn(ft.Text("Qty", weight=ft.FontWeight.W_600, size=12), numeric=True),
                ft.DataColumn(ft.Text("Total", weight=ft.FontWeight.W_600, size=12), numeric=True),
                ft.DataColumn(ft.Text("", size=12)),
            ],
            rows=[],
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=8,
            heading_row_color=ft.Colors.with_opacity(0.05, ft.Colors.BLACK),
            column_spacing=16,
        )

        # --- Totals ---
        self.subtotal_text = ft.Text("Subtotal: Rs. 0.00", size=16, weight=ft.FontWeight.W_600)
        self.discount_field = ft.TextField(
            label="Discount (Rs.)", value="0", width=150,
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=self._update_totals_display,
            border_radius=8,
        )
        self.grand_total_text = ft.Text("Grand Total: Rs. 0.00", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_700)
        self.payment_type = ft.Dropdown(
            label="Payment", value="Cash", width=150, border_radius=8,
            options=[
                ft.dropdown.Option("Cash"),
                ft.dropdown.Option("Credit"),
                ft.dropdown.Option("Online"),
            ],
        )

        self.complete_btn = ft.ElevatedButton(
            "Complete Sale",
            icon=ft.Icons.CHECK_CIRCLE,
            on_click=self._complete_sale,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.GREEN_700,
                color=ft.Colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=8),
            ),
        )
        self.clear_btn = ft.OutlinedButton(
            "Clear Cart",
            icon=ft.Icons.DELETE_SWEEP,
            on_click=self._clear_cart,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
        )

        self.status_text = ft.Text("", size=13)

        # --- Bill preview + print ---
        self.bill_preview = ft.Container(visible=False)
        self._last_sale_id = None

    def did_mount(self):
        self._build_controls()

    def _build_controls(self):
        search_card = ft.Container(
            content=ft.Column([
                ft.Text("Search & Add to Cart", size=18, weight=ft.FontWeight.BOLD),
                ft.Row([self.search_field], spacing=8),
                self.search_results,
            ], spacing=10),
            padding=20,
            border_radius=12,
            bgcolor=ft.Colors.WHITE,
            shadow=ft.BoxShadow(spread_radius=0, blur_radius=8, color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK), offset=ft.Offset(0, 2)),
        )

        cart_card = ft.Container(
            content=ft.Column([
                ft.Text("Cart", size=18, weight=ft.FontWeight.BOLD),
                self.cart_table,
                ft.Divider(height=1),
                self.subtotal_text,
                ft.Row([self.discount_field, self.payment_type], spacing=12),
                self.grand_total_text,
                ft.Row([self.complete_btn, self.clear_btn, self.status_text], spacing=12),
            ], spacing=10),
            padding=20,
            border_radius=12,
            bgcolor=ft.Colors.WHITE,
            shadow=ft.BoxShadow(spread_radius=0, blur_radius=8, color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK), offset=ft.Offset(0, 2)),
        )

        self.controls = [
            ft.Container(
                content=ft.Column([
                    ft.Text("Point of Sale", size=28, weight=ft.FontWeight.BOLD),
                    search_card,
                    cart_card,
                    self.bill_preview,
                ], spacing=20),
                padding=24,
            )
        ]
        self.update()

    def _do_search(self, e):
        query = self.search_field.value.strip()
        if len(query) < 1:
            self.search_results.controls = []
            self.search_results.update()
            return

        results = search_stock(query)
        items = []
        for r in results[:20]:
            row = ft.Container(
                content=ft.Row([
                    ft.Text(f"{r['product_name']}", weight=ft.FontWeight.W_600, size=13, expand=True),
                    ft.Text(f"Batch: {r['batch_no']}", size=12, color=ft.Colors.GREY_600),
                    ft.Text(f"Qty: {r['qty']}", size=12, color=ft.Colors.GREY_600),
                    ft.Text(f"MRP: Rs. {r['mrp']:.2f}", size=13, weight=ft.FontWeight.W_600, color=ft.Colors.BLUE_700),
                    ft.IconButton(
                        icon=ft.Icons.ADD_CIRCLE,
                        icon_color=ft.Colors.GREEN_700,
                        tooltip="Add to cart",
                        data=r,
                        on_click=self._add_to_cart,
                    ),
                ], alignment=ft.MainAxisAlignment.START, spacing=12),
                padding=ft.padding.symmetric(horizontal=12, vertical=6),
                border_radius=8,
                bgcolor=ft.Colors.GREY_50,
            )
            items.append(row)

        if not items:
            items.append(ft.Text("No results found.", italic=True, color=ft.Colors.GREY_500, size=13))

        self.search_results.controls = items
        self.search_results.update()

    def _add_to_cart(self, e):
        """Add a stock item to the cart (qty=1, price=MRP by default)."""
        r = e.control.data
        # Check if already in cart
        for item in self.cart:
            if item["stock_id"] == r["id"]:
                if item["qty"] < r["qty"]:
                    item["qty"] += 1
                    self._refresh_cart_ui()
                else:
                    self.status_text.value = "❌ Not enough stock available."
                    self.status_text.color = ft.Colors.RED_700
                    self.status_text.update()
                return

        # Default sell price = MRP (user can edit in cart)
        self.cart.append({
            "stock_id": r["id"],
            "product_name": r["product_name"],
            "batch_no": r["batch_no"],
            "qty": 1,
            "unit_price": r["mrp"],  # Editable by user
            "mrp": r["mrp"],
            "max_qty": r["qty"],
        })
        self._refresh_cart_ui()

    def _refresh_cart_ui(self):
        """Rebuild the cart table rows and update totals."""
        rows = []
        for i, item in enumerate(self.cart):
            line_total = item["qty"] * item["unit_price"]

            # Editable sell price field
            price_field = ft.TextField(
                value=f"{item['unit_price']:.2f}",
                width=90,
                text_size=12,
                content_padding=ft.padding.symmetric(horizontal=8, vertical=4),
                border_radius=6,
                keyboard_type=ft.KeyboardType.NUMBER,
                data=i,
                on_blur=self._on_price_change,
                on_submit=self._on_price_change,
            )

            rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(item["product_name"], size=12)),
                ft.DataCell(ft.Text(item["batch_no"], size=12)),
                ft.DataCell(ft.Text(f"Rs. {item['mrp']:.2f}", size=12, color=ft.Colors.GREY_600)),
                ft.DataCell(price_field),
                ft.DataCell(ft.Row([
                    ft.IconButton(ft.Icons.REMOVE_CIRCLE_OUTLINE, icon_size=18,
                                  data=i, on_click=self._dec_qty, tooltip="Decrease"),
                    ft.Text(str(item["qty"]), size=13, weight=ft.FontWeight.W_600),
                    ft.IconButton(ft.Icons.ADD_CIRCLE_OUTLINE, icon_size=18,
                                  data=i, on_click=self._inc_qty, tooltip="Increase"),
                ], spacing=0)),
                ft.DataCell(ft.Text(f"Rs. {line_total:.2f}", size=12, weight=ft.FontWeight.W_600)),
                ft.DataCell(ft.IconButton(
                    ft.Icons.DELETE, icon_size=18, icon_color=ft.Colors.RED_600,
                    data=i, on_click=self._remove_item, tooltip="Remove",
                )),
            ]))
        self.cart_table.rows = rows
        self._update_totals_display(None)
        self.update()

    def _on_price_change(self, e):
        """Update sell price when user edits it in the cart."""
        idx = e.control.data
        try:
            new_price = float(e.control.value or 0)
            self.cart[idx]["unit_price"] = new_price
            self._update_totals_display(None)
            self.update()
        except (ValueError, IndexError):
            pass

    def _inc_qty(self, e):
        idx = e.control.data
        if self.cart[idx]["qty"] < self.cart[idx]["max_qty"]:
            self.cart[idx]["qty"] += 1
        self._refresh_cart_ui()

    def _dec_qty(self, e):
        idx = e.control.data
        if self.cart[idx]["qty"] > 1:
            self.cart[idx]["qty"] -= 1
        self._refresh_cart_ui()

    def _remove_item(self, e):
        idx = e.control.data
        self.cart.pop(idx)
        self._refresh_cart_ui()

    def _update_totals_display(self, e):
        subtotal = sum(item["qty"] * item["unit_price"] for item in self.cart)
        try:
            discount = float(self.discount_field.value or 0)
        except ValueError:
            discount = 0
        grand = subtotal - discount
        self.subtotal_text.value = f"Subtotal: Rs. {subtotal:,.2f}"
        self.grand_total_text.value = f"Grand Total: Rs. {grand:,.2f}"
        try:
            self.subtotal_text.update()
            self.grand_total_text.update()
        except Exception:
            pass

    def _clear_cart(self, e):
        self.cart.clear()
        self.bill_preview.visible = False
        self.status_text.value = ""
        self._refresh_cart_ui()

    def _complete_sale(self, e):
        """Finalize the sale: save to DB, reduce stock, show bill."""
        if not self.cart:
            self.status_text.value = "❌ Cart is empty."
            self.status_text.color = ft.Colors.RED_700
            self.status_text.update()
            return

        subtotal = sum(item["qty"] * item["unit_price"] for item in self.cart)
        try:
            discount = float(self.discount_field.value or 0)
        except ValueError:
            discount = 0
        grand_total = subtotal - discount
        bill_no = generate_bill_no()
        pay_type = self.payment_type.value or "Cash"

        items_for_db = [
            {"stock_id": it["stock_id"], "qty": it["qty"], "unit_price": it["unit_price"]}
            for it in self.cart
        ]

        sale_id = create_sale(bill_no, subtotal, discount, grand_total, pay_type, items_for_db)
        self._last_sale_id = sale_id

        # Generate bill preview
        self._show_bill(sale_id)

        self.cart.clear()
        self.status_text.value = f"✅ Sale {bill_no} completed!"
        self.status_text.color = ft.Colors.GREEN_700
        self._refresh_cart_ui()

    def _show_bill(self, sale_id):
        """Render an invoice-style bill preview with print button."""
        sale = get_sale_with_items(sale_id)
        if not sale:
            return

        settings = get_shop_settings()
        shop_name = settings.get("shop_name", "Medical Store")

        # Build text preview
        lines = []
        lines.append("=" * 72)
        lines.append(f"  {shop_name.upper()}")
        lines.append("  INVOICE")
        lines.append("=" * 72)
        lines.append(f"  Invoice No : {sale['bill_no']}        Date    : {sale['timestamp']}")
        lines.append(f"  Bill Type  : {sale['payment_type']}")
        lines.append("-" * 72)
        lines.append(f"{'S.N.':<5} {'Product Name':<20} {'Batch No.':<12} {'Exp.Date':<10} {'Qty':>5} {'Rate':>10} {'Amount':>10} {'MRP':>8}")
        lines.append("-" * 72)
        for i, item in enumerate(sale["items"], 1):
            name = item["product_name"][:18]
            batch = item.get("batch_no", "")[:10]
            exp = item.get("exp_date", "")
            if exp and len(exp) >= 7:
                # format YYYY-MM-DD → MM/YYYY
                try:
                    parts = exp.split("-")
                    exp = f"{parts[1]}/{parts[0]}"
                except (IndexError, ValueError):
                    pass
            qty = item["qty"]
            rate = item["unit_price"]
            amount = qty * rate
            mrp = item.get("mrp", 0)
            lines.append(f"{i:<5} {name:<20} {batch:<12} {exp:<10} {qty:>5} {rate:>10.2f} {amount:>10.2f} {mrp:>8.2f}")
        lines.append("-" * 72)
        lines.append(f"{'Sub Total':>58} {sale['subtotal']:>12.2f}")
        lines.append(f"{'Discount Amount':>58} {sale['discount']:>12.2f}")
        round_off = round(sale['grand_total']) - sale['grand_total']
        net_amount = sale['grand_total'] + round_off
        lines.append(f"{'Round Off':>58} {round_off:>12.2f}")
        lines.append(f"{'Net Amount (NPR)':>58} {net_amount:>12.2f}")
        lines.append("=" * 72)

        bill_text = "\n".join(lines)

        print_btn = ft.ElevatedButton(
            "🖨 Print Bill",
            icon=ft.Icons.PRINT,
            on_click=lambda _: self._print_bill(sale_id),
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.BLUE_700,
                color=ft.Colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=8),
            ),
        )

        self.bill_preview.content = ft.Column([
            ft.Row([
                ft.Text("Invoice Preview", size=18, weight=ft.FontWeight.BOLD),
                print_btn,
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Container(
                content=ft.Text(bill_text, font_family="Courier New, monospace", size=11),
                padding=16,
                border_radius=8,
                bgcolor=ft.Colors.GREY_100,
                border=ft.border.all(1, ft.Colors.GREY_400),
            ),
        ], spacing=8)
        self.bill_preview.visible = True
        self.bill_preview.update()

    def _print_bill(self, sale_id):
        """Generate a printable HTML invoice matching the reference bill format."""
        sale = get_sale_with_items(sale_id)
        if not sale:
            return

        settings = get_shop_settings()
        shop_name = settings.get("shop_name", "Medical Store")
        logo_path = settings.get("logo_path", "")

        # Build logo as base64 data URI
        logo_html = ""
        if logo_path and os.path.exists(logo_path):
            try:
                with open(logo_path, "rb") as f:
                    logo_data = base64.b64encode(f.read()).decode()
                ext = os.path.splitext(logo_path)[1].lower().lstrip(".")
                mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "gif": "image/gif", "svg": "image/svg+xml"}.get(ext, "image/png")
                logo_html = f'<img src="data:{mime};base64,{logo_data}" style="max-height:70px;" />'
            except Exception:
                pass

        # Format invoice date
        inv_date = sale['timestamp']

        # Build items rows
        items_html = ""
        for i, item in enumerate(sale["items"], 1):
            exp = item.get("exp_date", "")
            if exp and "-" in exp:
                try:
                    parts = exp.split("-")
                    exp = f"{parts[1]}/{parts[0]}"
                except (IndexError, ValueError):
                    pass
            amount = item["qty"] * item["unit_price"]
            mrp = item.get("mrp", 0)
            packing = item.get("category", "")
            items_html += f"""
            <tr>
                <td class="c">{i}</td>
                <td class="l">{item['product_name']}</td>
                <td class="c">{packing}</td>
                <td class="c">{item.get('batch_no', '')}</td>
                <td class="c">{exp}</td>
                <td class="c">{item['qty']}</td>
                <td class="r">{item['unit_price']:.2f}</td>
                <td class="r">{amount:.2f}</td>
                <td class="r">{mrp:.2f}</td>
            </tr>"""

        # Round off calculation
        round_off = round(sale['grand_total']) - sale['grand_total']
        net_amount = sale['grand_total'] + round_off

        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8"/>
    <title>Invoice - {sale['bill_no']}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: Arial, Helvetica, sans-serif; font-size: 12px; padding: 15px; color: #000; }}
        .invoice-box {{ max-width: 900px; margin: 0 auto; border: 2px solid #000; }}

        /* --- Header --- */
        .header {{ display: flex; align-items: center; padding: 12px 16px; border-bottom: 2px solid #000; }}
        .header .logo {{ flex: 0 0 80px; margin-right: 16px; }}
        .header .logo img {{ max-height: 70px; max-width: 75px; }}
        .header .shop-info {{ flex: 1; text-align: center; }}
        .header .shop-info h1 {{ font-size: 22px; font-weight: bold; margin-bottom: 4px; letter-spacing: 1px; }}
        .header .shop-info p {{ font-size: 11px; color: #333; line-height: 1.5; }}

        /* --- Meta section --- */
        .meta {{ display: flex; border-bottom: 2px solid #000; }}
        .meta-left, .meta-right {{ flex: 1; padding: 8px 16px; }}
        .meta-right {{ border-left: 1px solid #000; }}
        .meta table {{ width: 100%; }}
        .meta td {{ padding: 2px 0; font-size: 12px; vertical-align: top; }}
        .meta td.label {{ font-weight: bold; width: 130px; }}
        .meta td.sep {{ width: 10px; text-align: center; }}
        .meta td.val {{ }}

        /* --- Items table --- */
        .items {{ width: 100%; border-collapse: collapse; }}
        .items th {{ background: #f0f0f0; border: 1px solid #000; padding: 5px 4px; font-size: 11px; font-weight: bold; text-align: center; }}
        .items td {{ border: 1px solid #777; padding: 4px; font-size: 11px; }}
        .items td.l {{ text-align: left; }}
        .items td.r {{ text-align: right; }}
        .items td.c {{ text-align: center; }}
        .items tbody tr:nth-child(even) {{ background: #fafafa; }}

        /* --- Totals --- */
        .totals-row {{ display: flex; border-top: 2px solid #000; }}
        .totals-left {{ flex: 1; padding: 8px 16px; font-size: 11px; border-right: 1px solid #000; }}
        .totals-right {{ flex: 0 0 280px; padding: 0; }}
        .totals-right table {{ width: 100%; border-collapse: collapse; }}
        .totals-right td {{ padding: 4px 10px; font-size: 12px; border-bottom: 1px solid #ddd; }}
        .totals-right td.lbl {{ text-align: right; font-weight: bold; }}
        .totals-right td.val {{ text-align: right; min-width: 100px; }}
        .totals-right tr.net td {{ font-size: 14px; font-weight: bold; border-top: 2px solid #000; border-bottom: none; background: #f0f0f0; }}

        .footer {{ text-align: center; padding: 8px; font-size: 11px; border-top: 1px solid #000; color: #555; }}

        @media print {{
            body {{ padding: 0; }}
            .invoice-box {{ border: none; }}
            .no-print {{ display: none; }}
        }}
    </style>
</head>
<body onload="window.print()">
<div class="invoice-box">

    <!-- HEADER: Logo + Shop Name -->
    <div class="header">
        <div class="logo">{logo_html}</div>
        <div class="shop-info">
            <h1>{shop_name.upper()}</h1>
        </div>
    </div>

    <!-- META: Customer info (left) + Invoice info (right) -->
    <div class="meta">
        <div class="meta-left">
            <div style="text-align:center; font-size:14px; font-weight:bold; border-bottom:1px solid #000; padding-bottom:4px; margin-bottom:6px;">INVOICE</div>
        </div>
        <div class="meta-right">
            <table>
                <tr><td class="label">Invoice No.</td><td class="sep">:</td><td class="val">{sale['bill_no']}</td></tr>
                <tr><td class="label">Invoice Date</td><td class="sep">:</td><td class="val">{inv_date}</td></tr>
                <tr><td class="label">Bill Type</td><td class="sep">:</td><td class="val">{sale['payment_type']}</td></tr>
            </table>
        </div>
    </div>

    <!-- ITEMS TABLE -->
    <table class="items">
        <thead>
            <tr>
                <th style="width:35px;">S.N.</th>
                <th style="min-width:150px;">Product Name</th>
                <th style="width:70px;">Packing</th>
                <th style="width:90px;">Batch No.</th>
                <th style="width:70px;">Exp. Date</th>
                <th style="width:40px;">Qty</th>
                <th style="width:80px;">Rate (NPR)</th>
                <th style="width:90px;">Amount (NPR)</th>
                <th style="width:70px;">MRP</th>
            </tr>
        </thead>
        <tbody>
            {items_html}
        </tbody>
    </table>

    <!-- TOTALS -->
    <div class="totals-row">
        <div class="totals-left">
            &nbsp;
        </div>
        <div class="totals-right">
            <table>
                <tr><td class="lbl">Sub Total</td><td class="val">{sale['subtotal']:,.2f}</td></tr>
                <tr><td class="lbl">Discount Amount</td><td class="val">{sale['discount']:,.2f}</td></tr>
                <tr><td class="lbl">Round Off</td><td class="val">{round_off:,.2f}</td></tr>
                <tr class="net"><td class="lbl">Net Amount (NPR) :</td><td class="val">{net_amount:,.2f}</td></tr>
            </table>
        </div>
    </div>

    <div class="footer">
        Thank you for your business!
    </div>

</div>
</body>
</html>"""

        # Write to temp file and open in browser for printing
        tmp_file = os.path.join(tempfile.gettempdir(), f"invoice_{sale['bill_no']}.html")
        with open(tmp_file, "w", encoding="utf-8") as f:
            f.write(html)

        webbrowser.open(f"file://{tmp_file}")

