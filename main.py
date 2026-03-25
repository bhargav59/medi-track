"""
main.py — Medi-Track Nepal v1.0  Entry Point
===============================================
Launches the Flet desktop application with:
  • A vertical NavigationRail sidebar (Dashboard, Inventory, POS, Reports, Suppliers).
  • Light-mode Material 3 theme with high contrast.
  • Auto-initializes the SQLite database on startup.

Run:  python main.py
"""

import flet as ft
from db_manager import initialize_database
from views.dashboard import DashboardView
from views.inventory import InventoryView
from views.pos import POSView
from views.reports import ReportsView
from views.suppliers import SuppliersView
from views.settings import SettingsView


def main(page: ft.Page):
    # ---- Page configuration ----
    page.title = "Medi-Track Nepal — Medical Store ERP"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.theme = ft.Theme(
        color_scheme_seed=ft.Colors.BLUE,
        use_material3=True,
    )
    page.padding = 0
    page.window.width = 1200
    page.window.height = 800

    # ---- Auto-initialize database ----
    initialize_database()

    # ---- View instances ----
    views: dict[int, ft.Control] = {}

    def get_view(index: int) -> ft.Control:
        """Lazily create and cache view instances."""
        if index not in views:
            if index == 0:
                views[index] = DashboardView(page)
            elif index == 1:
                views[index] = InventoryView(page)
            elif index == 2:
                views[index] = POSView(page)
            elif index == 3:
                views[index] = ReportsView(page)
            elif index == 4:
                views[index] = SuppliersView(page)
            elif index == 5:
                views[index] = SettingsView(page)
        return views[index]

    # ---- Content area ----
    content_area = ft.Container(
        content=get_view(0),
        expand=True,
        bgcolor=ft.Colors.GREY_100,
    )

    def on_nav_change(e):
        """Switch the content area to the selected view."""
        idx = e.control.selected_index
        content_area.content = get_view(idx)
        # Refresh dashboard when navigated to
        if idx == 0 and hasattr(views.get(0), "refresh_data"):
            views[0].refresh_data()
        content_area.update()

    # ---- Navigation Rail ----
    rail = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=80,
        min_extended_width=200,
        group_alignment=-0.9,
        on_change=on_nav_change,
        bgcolor=ft.Colors.WHITE,
        indicator_color=ft.Colors.BLUE_100,
        destinations=[
            ft.NavigationRailDestination(
                icon=ft.Icons.DASHBOARD_OUTLINED,
                selected_icon=ft.Icons.DASHBOARD,
                label="Dashboard",
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.INVENTORY_2_OUTLINED,
                selected_icon=ft.Icons.INVENTORY_2,
                label="Inventory",
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.POINT_OF_SALE_OUTLINED,
                selected_icon=ft.Icons.POINT_OF_SALE,
                label="POS",
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.ASSESSMENT_OUTLINED,
                selected_icon=ft.Icons.ASSESSMENT,
                label="Reports",
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.LOCAL_SHIPPING_OUTLINED,
                selected_icon=ft.Icons.LOCAL_SHIPPING,
                label="Suppliers",
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.SETTINGS_OUTLINED,
                selected_icon=ft.Icons.SETTINGS,
                label="Settings",
            ),
        ],
    )

    # ---- Main layout: sidebar + content ----
    page.add(
        ft.Row(
            [
                rail,
                ft.VerticalDivider(width=1),
                content_area,
            ],
            expand=True,
            spacing=0,
        )
    )


# ---- Entry point ----
if __name__ == "__main__":
    ft.app(main)
