"""
views/dashboard.py — Module A: The "Intelligence" Dashboard
============================================================
Displays:
  • Top bar: Today's Total Sales, Today's Profit, Total Items in stock.
  • Alerts panel:
      - Expiring soon (< 60 days) → ORANGE
      - Already expired → RED
      - Low stock → AMBER
"""

import flet as ft
from db_manager import (
    get_today_sales_total,
    get_today_profit,
    get_total_items_count,
    get_expiry_alerts,
    get_expired_items,
    get_low_stock_items,
)


def _stat_card(title: str, value: str, icon: str, color: str) -> ft.Container:
    """Build a single statistics card for the top bar."""
    return ft.Container(
        content=ft.Column(
            [
                ft.Icon(icon, size=32, color=color),
                ft.Text(title, size=13, weight=ft.FontWeight.W_500, color=ft.Colors.GREY_700),
                ft.Text(value, size=26, weight=ft.FontWeight.BOLD, color=color),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=4,
        ),
        padding=20,
        border_radius=12,
        bgcolor=ft.Colors.WHITE,
        shadow=ft.BoxShadow(
            spread_radius=0, blur_radius=8,
            color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK),
            offset=ft.Offset(0, 2),
        ),
        expand=True,
    )


def _alert_table(title: str, rows: list, color: str, columns: list[str]) -> ft.Container:
    """Build an alert section with a colored header and data table."""
    data_rows = []
    for r in rows[:50]:  # cap at 50 rows for performance
        cells = [ft.DataCell(ft.Text(str(r.get(c, "")), size=12)) for c in columns]
        data_rows.append(ft.DataRow(cells=cells))

    table = ft.DataTable(
        columns=[ft.DataColumn(ft.Text(c.replace("_", " ").title(), weight=ft.FontWeight.W_600, size=12)) for c in columns],
        rows=data_rows,
        border=ft.border.all(1, ft.Colors.GREY_300),
        border_radius=8,
        heading_row_color=ft.Colors.with_opacity(0.05, ft.Colors.BLACK),
        data_row_max_height=40,
        column_spacing=20,
    )

    count_badge = ft.Container(
        content=ft.Text(str(len(rows)), size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
        bgcolor=color,
        border_radius=10,
        padding=ft.padding.symmetric(horizontal=8, vertical=2),
    )

    return ft.Container(
        content=ft.Column(
            [
                ft.Row([
                    ft.Text(title, size=16, weight=ft.FontWeight.BOLD, color=color),
                    count_badge,
                ], alignment=ft.MainAxisAlignment.START, spacing=10),
                table if data_rows else ft.Text("No items.", size=13, italic=True, color=ft.Colors.GREY_500),
            ],
            spacing=8,
        ),
        padding=16,
        border_radius=12,
        bgcolor=ft.Colors.WHITE,
        shadow=ft.BoxShadow(
            spread_radius=0, blur_radius=6,
            color=ft.Colors.with_opacity(0.06, ft.Colors.BLACK),
            offset=ft.Offset(0, 2),
        ),
    )


class DashboardView(ft.Column):
    """Main dashboard view — assembled as a scrollable column."""

    def __init__(self, page: ft.Page):
        super().__init__()
        self._page_ref = page
        self.expand = True
        self.scroll = ft.ScrollMode.AUTO
        self.spacing = 20
        self.horizontal_alignment = ft.CrossAxisAlignment.STRETCH

    def did_mount(self):
        self.refresh_data()

    def refresh_data(self):
        """Reload all dashboard data from the database."""
        total_sales = get_today_sales_total()
        profit = get_today_profit()
        total_items = get_total_items_count()

        expiring = get_expiry_alerts(60)
        expired = get_expired_items()
        low_stock = get_low_stock_items()

        # ---- Top stat cards ----
        stats_row = ft.Row(
            [
                _stat_card("Today's Sales", f"Rs. {total_sales:,.2f}", ft.Icons.POINT_OF_SALE, ft.Colors.BLUE_700),
                _stat_card("Today's Profit", f"Rs. {profit:,.2f}", ft.Icons.TRENDING_UP, ft.Colors.GREEN_700),
                _stat_card("Items in Stock", str(total_items), ft.Icons.INVENTORY_2, ft.Colors.DEEP_PURPLE_600),
            ],
            spacing=16,
        )

        # ---- Alert panels ----
        expiring_panel = _alert_table(
            "⚠ Expiring Soon (< 60 Days)", expiring, ft.Colors.ORANGE_700,
            ["product_name", "batch_no", "exp_date", "qty"],
        )
        expired_panel = _alert_table(
            "🛑 Already Expired", expired, ft.Colors.RED_700,
            ["product_name", "batch_no", "exp_date", "qty"],
        )
        low_stock_panel = _alert_table(
            "📦 Low Stock Alert", low_stock, ft.Colors.AMBER_800,
            ["name", "total_qty", "min_stock_alert"],
        )

        refresh_btn = ft.ElevatedButton(
            "Refresh Dashboard",
            icon=ft.Icons.REFRESH,
            on_click=lambda _: self.refresh_data(),
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
        )

        self.controls = [
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text("Dashboard", size=28, weight=ft.FontWeight.BOLD),
                        refresh_btn,
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    stats_row,
                    expiring_panel,
                    expired_panel,
                    low_stock_panel,
                ], spacing=20),
                padding=24,
            )
        ]
        self.update()
