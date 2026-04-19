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
from datetime import datetime, date
from nepali_date import ad_to_bs_string, get_dual_date
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
                ft.DataColumn(ft.Text("Product Name", weight=ft.FontWeight.W_600, size=12)),
                ft.DataColumn(ft.Text("Batch", weight=ft.FontWeight.W_600, size=12)),
                ft.DataColumn(ft.Text("MRP", weight=ft.FontWeight.W_600, size=12), numeric=True),
                ft.DataColumn(ft.Text("Sell Price", weight=ft.FontWeight.W_600, size=12), numeric=True),
                ft.DataColumn(ft.Text("Qty", weight=ft.FontWeight.W_600, size=12), numeric=True),
                ft.DataColumn(ft.Text("Free", weight=ft.FontWeight.W_600, size=12), numeric=True),
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
            "free_qty": 0,
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

            # Editable free qty field
            free_field = ft.TextField(
                value=str(item.get("free_qty", 0)),
                width=55,
                text_size=12,
                content_padding=ft.padding.symmetric(horizontal=6, vertical=4),
                border_radius=6,
                keyboard_type=ft.KeyboardType.NUMBER,
                data=i,
                on_blur=self._on_free_change,
                on_submit=self._on_free_change,
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
                ft.DataCell(free_field),
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

    def _on_free_change(self, e):
        """Update free qty when user edits it in the cart."""
        idx = e.control.data
        try:
            free_val = int(float(e.control.value or 0))
            if free_val < 0:
                free_val = 0
            # Ensure free + paid qty doesn't exceed stock
            max_available = self.cart[idx]["max_qty"]
            if self.cart[idx]["qty"] + free_val > max_available:
                free_val = max(0, max_available - self.cart[idx]["qty"])
                e.control.value = str(free_val)
                e.control.update()
            self.cart[idx]["free_qty"] = free_val
        except (ValueError, IndexError):
            pass

    def _inc_qty(self, e):
        idx = e.control.data
        used = self.cart[idx]["qty"] + self.cart[idx].get("free_qty", 0)
        if used < self.cart[idx]["max_qty"]:
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
        """Show customer details dialog before completing the sale."""
        if not self.cart:
            self.status_text.value = "❌ Cart is empty."
            self.status_text.color = ft.Colors.RED_700
            self.status_text.update()
            return

        # Create customer detail fields
        self._cust_name = ft.TextField(label="Customer Name", border_radius=8, autofocus=True)
        self._cust_address = ft.TextField(label="Address", border_radius=8)
        self._cust_pan = ft.TextField(label="PAN / VAT No.", border_radius=8)
        self._cust_phone = ft.TextField(label="Phone No.", border_radius=8)

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Customer Details", weight=ft.FontWeight.BOLD),
            content=ft.Column([
                ft.Text("Enter customer details for the invoice (optional):", size=13, color=ft.Colors.GREY_600),
                self._cust_name,
                self._cust_address,
                self._cust_pan,
                self._cust_phone,
            ], spacing=10, tight=True, width=400),
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: self._close_dialog()),
                ft.ElevatedButton(
                    "Complete Sale",
                    icon=ft.Icons.CHECK_CIRCLE,
                    on_click=lambda _: self._finalize_sale(),
                    style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        # Flet 0.82+: use show_dialog / pop_dialog instead of overlay
        self._page_ref.show_dialog(dlg)

    def _close_dialog(self):
        self._page_ref.pop_dialog()

    def _finalize_sale(self):
        """Actually finalize the sale after customer dialog."""
        cust_name = self._cust_name.value.strip() if self._cust_name.value else ""
        cust_address = self._cust_address.value.strip() if self._cust_address.value else ""
        cust_pan = self._cust_pan.value.strip() if self._cust_pan.value else ""
        cust_phone = self._cust_phone.value.strip() if self._cust_phone.value else ""

        # Close dialog first
        self._page_ref.pop_dialog()

        subtotal = sum(item["qty"] * item["unit_price"] for item in self.cart)
        try:
            discount = float(self.discount_field.value or 0)
        except ValueError:
            discount = 0
        grand_total = subtotal - discount
        bill_no = generate_bill_no()
        pay_type = self.payment_type.value or "Cash"

        items_for_db = [
            {"stock_id": it["stock_id"], "qty": it["qty"], "free_qty": it.get("free_qty", 0), "unit_price": it["unit_price"]}
            for it in self.cart
        ]

        sale_id = create_sale(bill_no, subtotal, discount, grand_total, pay_type, items_for_db,
                              customer_name=cust_name, customer_address=cust_address,
                              customer_pan=cust_pan, customer_phone=cust_phone)
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
        """Generate a printable HTML invoice exactly matching the reference bill format."""
        sale = get_sale_with_items(sale_id)
        if not sale:
            return

        settings = get_shop_settings()
        shop_name = settings.get("shop_name", "Medical Store")
        shop_address = settings.get("shop_address", "")
        shop_phone = settings.get("shop_phone", "")
        shop_email = settings.get("shop_email", "")
        shop_pan = settings.get("shop_pan", "")
        bank_details = settings.get("bank_details", "")
        logo_path = settings.get("logo_path", "")

        # Build logo as base64 data URI
        logo_html = ""
        if logo_path and os.path.exists(logo_path):
            try:
                with open(logo_path, "rb") as f:
                    logo_data = base64.b64encode(f.read()).decode()
                ext = os.path.splitext(logo_path)[1].lower().lstrip(".")
                mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "gif": "image/gif"}.get(ext, "image/png")
                logo_html = f'<img src="data:{mime};base64,{logo_data}" />'
            except Exception:
                pass

        inv_date = sale['timestamp']
        # Generate BS date for invoice
        inv_date_ad = inv_date[:10]  # YYYY-MM-DD
        bs_date = ad_to_bs_string(inv_date_ad)
        dual_date = get_dual_date(inv_date_ad)
        # AD date formatted as MM/DD/YYYY
        try:
            ad_parts = inv_date_ad.split('-')
            ad_formatted = f"{ad_parts[1]}/{ad_parts[2]}/{ad_parts[0]}"
        except (IndexError, ValueError):
            ad_formatted = inv_date_ad

        # Customer details from sale
        cust_name = sale.get('customer_name', '')
        cust_address = sale.get('customer_address', '')
        cust_pan = sale.get('customer_pan', '')
        cust_phone = sale.get('customer_phone', '')

        # Build shop contact line
        email_phone_line = ""
        if shop_email:
            email_phone_line += f"Email : {shop_email}"
        if shop_phone:
            if email_phone_line:
                email_phone_line += f"&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;"
            email_phone_line += f"Phone No. : {shop_phone}"
        pan_line = f"PAN : {shop_pan}" if shop_pan else ""

        # Build items rows
        items_html = ""
        num_items = len(sale["items"])
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
                <td class="c">{item.get('free_qty', 0)}</td>
                <td class="r">{item['unit_price']:,.2f}</td>
                <td class="r">{amount:,.2f}</td>
                <td class="r">{mrp:,.2f}</td>
            </tr>"""

        # Add empty rows to fill table like the reference (minimum ~20 rows)
        for j in range(num_items + 1, 21):
            items_html += """
            <tr>
                <td class="c">&nbsp;</td><td class="l">&nbsp;</td><td class="c"></td>
                <td class="c"></td><td class="c"></td><td class="c"></td>
                <td class="c"></td><td class="r"></td><td class="r"></td><td class="r"></td>
            </tr>"""

        # Round off & net amount
        round_off = round(sale['grand_total']) - sale['grand_total']
        net_amount = round(sale['grand_total'])

        # Amount in words
        net_int = int(net_amount)
        amount_words = self._amount_to_words(net_int)

        # Bank details (multiline → <br>)
        bank_html = bank_details.replace("\n", "<br/>") if bank_details else ""

        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8"/>
    <title>Invoice - {sale['bill_no']}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: Arial, Helvetica, sans-serif; font-size: 12px; padding: 10px; color: #000; }}
        .inv {{ max-width: 960px; margin: 0 auto; border: 2px solid #000; }}

        /* HEADER */
        .hdr {{ display: flex; align-items: center; padding: 10px 14px; border-bottom: 2px solid #000; }}
        .hdr .logo {{ flex: 0 0 90px; text-align: center; }}
        .hdr .logo img {{ max-height: 75px; max-width: 80px; }}
        .hdr .info {{ flex: 1; text-align: center; }}
        .hdr .info h1 {{ font-size: 22px; font-weight: bold; letter-spacing: 1px; margin-bottom: 2px; }}
        .hdr .info .loc {{ font-size: 12px; font-weight: bold; margin-bottom: 2px; }}
        .hdr .info .contact {{ font-size: 10px; color: #333; }}

        /* META SECTION */
        .meta {{ display: flex; border-bottom: 2px solid #000; font-size: 12px; }}
        .meta-left {{ flex: 1; padding: 6px 12px; border-right: 1px solid #000; }}
        .meta-right {{ flex: 1; padding: 6px 12px; }}
        .meta td {{ padding: 1px 0; }}
        .meta td.lbl {{ font-weight: bold; width: 120px; }}
        .meta td.sep {{ width: 12px; text-align: center; }}

        /* TRANSPORT / CN ROW */
        .transport-row {{ display: flex; border-bottom: 2px solid #000; font-size: 11px; padding: 3px 12px; }}
        .transport-row span {{ margin-right: 30px; }}

        /* ITEMS TABLE */
        .items {{ width: 100%; border-collapse: collapse; }}
        .items th {{ background: #e8e8e8; border: 1px solid #000; padding: 4px 3px; font-size: 10.5px; font-weight: bold; text-align: center; }}
        .items td {{ border: 1px solid #999; padding: 3px 4px; font-size: 10.5px; }}
        .items td.l {{ text-align: left; }}
        .items td.r {{ text-align: right; }}
        .items td.c {{ text-align: center; }}

        /* TOTALS FOOTER */
        .footer-row {{ display: flex; border-top: 2px solid #000; }}
        .footer-left {{ flex: 1; padding: 6px 12px; font-size: 11px; border-right: 1px solid #000; }}
        .footer-left .bank-title {{ font-weight: bold; margin-bottom: 2px; }}
        .footer-right {{ flex: 0 0 290px; }}
        .footer-right table {{ width: 100%; border-collapse: collapse; }}
        .footer-right td {{ padding: 3px 8px; font-size: 12px; border-bottom: 1px solid #ccc; }}
        .footer-right td.lbl {{ text-align: right; font-weight: bold; }}
        .footer-right td.val {{ text-align: right; width: 110px; }}
        .footer-right tr.net td {{ font-size: 13px; font-weight: bold; border-top: 2px solid #000; border-bottom: 2px solid #000; background: #f0f0f0; }}

        .words-row {{ padding: 4px 12px; font-size: 11px; border-top: 1px solid #000; font-style: italic; }}
        .notice {{ padding: 4px 12px; font-size: 10px; text-align: right; color: #555; border-top: 1px solid #ddd; }}

        @media print {{
            body {{ padding: 0; margin: 0; }}
            .inv {{ border: none; }}
            .no-print {{ display: none !important; }}
            @page {{ margin: 5mm; }}
        }}
    </style>
</head>
<body>
<script>
    window.onload = function() {
        window.print();
        // Auto-close tab after print dialog closes
        window.addEventListener('afterprint', function() { window.close(); });
        // Fallback: close when window regains focus (user cancelled print)
        setTimeout(function() { window.onfocus = function() { window.close(); }; }, 500);
    };
</script>
<div class="inv">

    <!-- HEADER -->
    <div class="hdr">
        <div class="logo">{logo_html}</div>
        <div class="info">
            <h1>{shop_name.upper()}</h1>
            {"<div class='loc'>" + shop_address.upper() + "</div>" if shop_address else ""}
            <div class="contact">
                {email_phone_line}
                {"<br/>" + pan_line if pan_line else ""}
            </div>
            <div style="font-size:16px; font-weight:bold; text-decoration:underline; margin-top:4px; letter-spacing:2px;">INVOICE</div>
        </div>
    </div>

    <!-- META: Customer (left) | Invoice details (right) -->
    <div class="meta">
        <div class="meta-left">
            <table>
                <tr><td class="lbl">CUSTOMER NAME</td><td class="sep">:</td><td><b>{cust_name}</b></td></tr>
                <tr><td class="lbl">Address</td><td class="sep">:</td><td>{cust_address}</td></tr>
                <tr><td class="lbl">PAN / VAT</td><td class="sep">:</td><td>{cust_pan}</td></tr>
                <tr><td class="lbl">Phone No.</td><td class="sep">:</td><td>{cust_phone}</td></tr>
            </table>
        </div>
        <div class="meta-right">
            <table>
                <tr><td class="lbl">Invoice No.</td><td class="sep">:</td><td>{sale['bill_no']}</td></tr>
                <tr><td class="lbl">Invoice Date</td><td class="sep">:</td><td>{bs_date}&nbsp;&nbsp;{ad_formatted}</td></tr>
                <tr><td class="lbl">Bill Type</td><td class="sep">:</td><td>{sale['payment_type']}</td></tr>
                <tr><td class="lbl">Transaction Date</td><td class="sep">:</td><td>{ad_formatted}</td></tr>
            </table>
        </div>
    </div>

    <!-- TRANSPORT / CN ROW -->
    <div class="transport-row">
        <span><b>Transport:</b> __________</span>
        <span><b>C.N. NO.:</b> __________</span>
        <span style="margin-left:auto"><b>No. of Cases:</b> {len(sale['items'])}</span>
    </div>

    <!-- ITEMS TABLE -->
    <table class="items">
        <thead>
            <tr>
                <th style="width:30px">S.N.</th>
                <th style="min-width:140px">Product Name</th>
                <th style="width:60px">Packing</th>
                <th style="width:80px">Batch No.</th>
                <th style="width:65px">Exp. Date</th>
                <th style="width:35px">Qty</th>
                <th style="width:40px">Free</th>
                <th style="width:75px">Rate (NPR)</th>
                <th style="width:85px">Amount (NPR)</th>
                <th style="width:65px">MRP</th>
            </tr>
        </thead>
        <tbody>
            {items_html}
        </tbody>
    </table>

    <!-- TOTALS FOOTER -->
    <div class="footer-row">
        <div class="footer-left">
            {"<div class='bank-title'>Bank Details:</div><div>" + bank_html + "</div>" if bank_html else "&nbsp;"}
        </div>
        <div class="footer-right">
            <table>
                <tr><td class="lbl">Sub Total</td><td class="val">{sale['subtotal']:,.2f}</td></tr>
                <tr><td class="lbl">Discount Amount :</td><td class="val">{sale['discount']:,.2f}</td></tr>
                <tr><td class="lbl">Round Off</td><td class="val">{round_off:,.2f}</td></tr>
                <tr class="net"><td class="lbl">Net Amount (NPR) :</td><td class="val">{net_amount:,.2f}</td></tr>
            </table>
        </div>
    </div>

    <!-- AMOUNT IN WORDS -->
    <div class="words-row">
        <b>In Words:</b> Nepalese Rupees {amount_words} Only
    </div>

    <!-- NOTICE -->
    <div class="notice">
        Medicine once sold and lot bonus is not returnable.
    </div>

</div>
</body>
</html>"""

        # Write to temp file and open in browser for printing
        tmp_file = os.path.join(tempfile.gettempdir(), f"invoice_{sale['bill_no']}.html")
        with open(tmp_file, "w", encoding="utf-8") as f:
            f.write(html)

        webbrowser.open(f"file://{tmp_file}")

    @staticmethod
    def _amount_to_words(n):
        """Convert an integer amount to English words (Nepali invoice style)."""
        if n == 0:
            return "Zero"
        ones = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
                "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen",
                "Seventeen", "Eighteen", "Nineteen"]
        tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]

        def two_digits(num):
            if num < 20:
                return ones[num]
            return tens[num // 10] + ("-" + ones[num % 10] if num % 10 else "")

        def three_digits(num):
            if num >= 100:
                return ones[num // 100] + " Hundred" + (" " + two_digits(num % 100) if num % 100 else "")
            return two_digits(num)

        parts = []
        if n >= 10000000:
            parts.append(two_digits(n // 10000000) + " Crore")
            n %= 10000000
        if n >= 100000:
            parts.append(two_digits(n // 100000) + " Lakh")
            n %= 100000
        if n >= 1000:
            parts.append(two_digits(n // 1000) + " Thousand")
            n %= 1000
        if n >= 100:
            parts.append(three_digits(n))
        elif n > 0:
            parts.append(two_digits(n))

        return " ".join(parts)


