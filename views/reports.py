"""
views/reports.py — Module D: Reporting
========================================
Features:
  • Monthly Sales Report: filter by date range (calendar pickers), see bill totals.
  • Expiry Audit: filter by date range to find items to return to suppliers.
"""

import flet as ft
from datetime import datetime, timedelta
from db_manager import get_sales_report, get_expiry_audit


class ReportsView(ft.Column):
    """Reports view: sales reports and expiry audits."""

    def __init__(self, page: ft.Page):
        super().__init__()
        self._page_ref = page
        self.expand = True
        self.scroll = ft.ScrollMode.AUTO
        self.spacing = 20

        # Default date range: this month
        today = datetime.now()
        first_of_month = today.replace(day=1)

        # Start date with calendar picker
        self.start_date_display = ft.TextField(
            label="Start Date",
            value=first_of_month.strftime("%d/%m/%Y"),
            read_only=True, width=180, border_radius=8,
        )
        self._start_iso = first_of_month.strftime("%Y-%m-%d")
        self.start_date_picker = ft.DatePicker(
            value=first_of_month,
            first_date=datetime(2020, 1, 1),
            last_date=datetime(2050, 12, 31),
            on_change=self._on_start_picked,
        )
        self.start_date_btn = ft.IconButton(
            icon=ft.Icons.CALENDAR_MONTH,
            tooltip="Pick Start Date",
            on_click=self._open_start_picker,
        )

        # End date with calendar picker
        self.end_date_display = ft.TextField(
            label="End Date",
            value=today.strftime("%d/%m/%Y"),
            read_only=True, width=180, border_radius=8,
        )
        self._end_iso = today.strftime("%Y-%m-%d")
        self.end_date_picker = ft.DatePicker(
            value=today,
            first_date=datetime(2020, 1, 1),
            last_date=datetime(2050, 12, 31),
            on_change=self._on_end_picked,
        )
        self.end_date_btn = ft.IconButton(
            icon=ft.Icons.CALENDAR_MONTH,
            tooltip="Pick End Date",
            on_click=self._open_end_picker,
        )

        self.sales_btn = ft.ElevatedButton(
            "Generate Sales Report",
            icon=ft.Icons.RECEIPT_LONG,
            on_click=self._gen_sales_report,
            style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_700, color=ft.Colors.WHITE, shape=ft.RoundedRectangleBorder(radius=8)),
        )
        self.expiry_btn = ft.ElevatedButton(
            "Generate Expiry Audit",
            icon=ft.Icons.WARNING_AMBER,
            on_click=self._gen_expiry_audit,
            style=ft.ButtonStyle(bgcolor=ft.Colors.ORANGE_700, color=ft.Colors.WHITE, shape=ft.RoundedRectangleBorder(radius=8)),
        )

        self.report_area = ft.Column(spacing=8)
        self.status_text = ft.Text("", size=13)

    def did_mount(self):
        # Register date pickers with the page overlay
        self._page_ref.overlay.append(self.start_date_picker)
        self._page_ref.overlay.append(self.end_date_picker)
        self._page_ref.update()
        self._build_controls()

    # ---- Calendar picker handlers ----
    def _open_start_picker(self, e):
        self.start_date_picker.open = True
        self._page_ref.update()

    def _on_start_picked(self, e):
        if e.control.value:
            dt = e.control.value
            self._start_iso = dt.strftime("%Y-%m-%d")
            self.start_date_display.value = dt.strftime("%d/%m/%Y")
            self.start_date_display.update()

    def _open_end_picker(self, e):
        self.end_date_picker.open = True
        self._page_ref.update()

    def _on_end_picked(self, e):
        if e.control.value:
            dt = e.control.value
            self._end_iso = dt.strftime("%Y-%m-%d")
            self.end_date_display.value = dt.strftime("%d/%m/%Y")
            self.end_date_display.update()

    def _build_controls(self):
        start_row = ft.Row([self.start_date_display, self.start_date_btn], spacing=4)
        end_row = ft.Row([self.end_date_display, self.end_date_btn], spacing=4)

        filter_card = ft.Container(
            content=ft.Column([
                ft.Text("Report Filters", size=18, weight=ft.FontWeight.BOLD),
                ft.Row([start_row, end_row], spacing=12),
                ft.Row([self.sales_btn, self.expiry_btn, self.status_text], spacing=12),
            ], spacing=12),
            padding=20,
            border_radius=12,
            bgcolor=ft.Colors.WHITE,
            shadow=ft.BoxShadow(spread_radius=0, blur_radius=8, color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK), offset=ft.Offset(0, 2)),
        )

        result_card = ft.Container(
            content=self.report_area,
            padding=20,
            border_radius=12,
            bgcolor=ft.Colors.WHITE,
            shadow=ft.BoxShadow(spread_radius=0, blur_radius=8, color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK), offset=ft.Offset(0, 2)),
        )

        self.controls = [
            ft.Container(
                content=ft.Column([
                    ft.Text("Reports", size=28, weight=ft.FontWeight.BOLD),
                    filter_card,
                    result_card,
                ], spacing=20),
                padding=24,
            )
        ]
        self.update()

    def _gen_sales_report(self, e):
        sd = self._start_iso
        ed = self._end_iso
        if not sd or not ed:
            self.status_text.value = "❌ Please select both dates."
            self.status_text.color = ft.Colors.RED_700
            self.status_text.update()
            return

        sales = get_sales_report(sd, ed)
        if not sales:
            self.report_area.controls = [ft.Text("No sales found for this period.", italic=True, color=ft.Colors.GREY_500)]
            self.report_area.update()
            return

        total_revenue = sum(s["grand_total"] for s in sales)

        table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Bill No", weight=ft.FontWeight.W_600, size=12)),
                ft.DataColumn(ft.Text("Date/Time", weight=ft.FontWeight.W_600, size=12)),
                ft.DataColumn(ft.Text("Subtotal", weight=ft.FontWeight.W_600, size=12), numeric=True),
                ft.DataColumn(ft.Text("Discount", weight=ft.FontWeight.W_600, size=12), numeric=True),
                ft.DataColumn(ft.Text("Grand Total", weight=ft.FontWeight.W_600, size=12), numeric=True),
                ft.DataColumn(ft.Text("Payment", weight=ft.FontWeight.W_600, size=12)),
            ],
            rows=[
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(s["bill_no"], size=12)),
                    ft.DataCell(ft.Text(s["timestamp"], size=12)),
                    ft.DataCell(ft.Text(f"Rs. {s['subtotal']:.2f}", size=12)),
                    ft.DataCell(ft.Text(f"Rs. {s['discount']:.2f}", size=12)),
                    ft.DataCell(ft.Text(f"Rs. {s['grand_total']:.2f}", size=12, weight=ft.FontWeight.W_600)),
                    ft.DataCell(ft.Text(s["payment_type"], size=12)),
                ]) for s in sales
            ],
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=8,
            heading_row_color=ft.Colors.with_opacity(0.05, ft.Colors.BLACK),
            column_spacing=18,
        )

        self.report_area.controls = [
            ft.Text("📊 Sales Report", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_700),
            ft.Text(f"Total Revenue: Rs. {total_revenue:,.2f}", size=16, weight=ft.FontWeight.W_600),
            ft.Text(f"Transactions: {len(sales)}", size=14),
            table,
        ]
        self.status_text.value = ""
        self.report_area.update()
        self.status_text.update()

    def _gen_expiry_audit(self, e):
        sd = self._start_iso
        ed = self._end_iso
        if not sd or not ed:
            self.status_text.value = "❌ Please select both dates."
            self.status_text.color = ft.Colors.RED_700
            self.status_text.update()
            return

        items = get_expiry_audit(sd, ed)
        if not items:
            self.report_area.controls = [ft.Text("No expiring items found for this period.", italic=True, color=ft.Colors.GREY_500)]
            self.report_area.update()
            return

        table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Product", weight=ft.FontWeight.W_600, size=12)),
                ft.DataColumn(ft.Text("Batch", weight=ft.FontWeight.W_600, size=12)),
                ft.DataColumn(ft.Text("Exp Date", weight=ft.FontWeight.W_600, size=12)),
                ft.DataColumn(ft.Text("Qty", weight=ft.FontWeight.W_600, size=12), numeric=True),
                ft.DataColumn(ft.Text("Supplier", weight=ft.FontWeight.W_600, size=12)),
            ],
            rows=[
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(str(it.get("product_name", "")), size=12)),
                    ft.DataCell(ft.Text(str(it.get("batch_no", "")), size=12)),
                    ft.DataCell(ft.Text(str(it.get("exp_date", "")), size=12)),
                    ft.DataCell(ft.Text(str(it.get("qty", 0)), size=12)),
                    ft.DataCell(ft.Text(str(it.get("supplier_name", "N/A")), size=12)),
                ]) for it in items
            ],
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=8,
            heading_row_color=ft.Colors.with_opacity(0.05, ft.Colors.BLACK),
            column_spacing=18,
        )

        self.report_area.controls = [
            ft.Text("⚠ Expiry Audit", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.ORANGE_700),
            ft.Text(f"Items found: {len(items)}", size=14),
            table,
        ]
        self.status_text.value = ""
        self.report_area.update()
        self.status_text.update()
