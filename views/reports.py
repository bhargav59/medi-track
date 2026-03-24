"""
views/reports.py — Module D: Reporting
========================================
Features:
  • Monthly Sales Report: filter by date range, see bill totals.
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

        self.start_date = ft.TextField(
            label="Start Date (DD/MM/YYYY)",
            value=first_of_month.strftime("%d/%m/%Y"),
            width=200, border_radius=8,
        )
        self.end_date = ft.TextField(
            label="End Date (DD/MM/YYYY)",
            value=today.strftime("%d/%m/%Y"),
            width=200, border_radius=8,
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
        self._build_controls()

    def _build_controls(self):
        filter_card = ft.Container(
            content=ft.Column([
                ft.Text("Report Filters", size=18, weight=ft.FontWeight.BOLD),
                ft.Row([self.start_date, self.end_date], spacing=12),
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

    def _parse_date(self, value):
        """Parse DD/MM/YYYY to YYYY-MM-DD string."""
        try:
            dt = datetime.strptime(value.strip(), "%d/%m/%Y")
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            return None

    def _gen_sales_report(self, e):
        sd = self._parse_date(self.start_date.value)
        ed = self._parse_date(self.end_date.value)
        if not sd or not ed:
            self.status_text.value = "❌ Invalid date format. Use DD/MM/YYYY."
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
        sd = self._parse_date(self.start_date.value)
        ed = self._parse_date(self.end_date.value)
        if not sd or not ed:
            self.status_text.value = "❌ Invalid date format. Use DD/MM/YYYY."
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
