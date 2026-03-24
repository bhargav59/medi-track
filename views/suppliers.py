"""
views/suppliers.py — Supplier Management
==========================================
Features:
  • Add / edit / delete suppliers.
  • Display supplier list with contact, address, outstanding dues.
"""

import flet as ft
from db_manager import (
    add_supplier,
    get_all_suppliers,
    update_supplier,
    delete_supplier,
)


class SuppliersView(ft.Column):
    """Supplier CRUD view."""

    def __init__(self, page: ft.Page):
        super().__init__()
        self._page_ref = page
        self.expand = True
        self.scroll = ft.ScrollMode.AUTO
        self.spacing = 20

        self.name_field = ft.TextField(label="Supplier Name", border_radius=8, expand=True)
        self.contact_field = ft.TextField(label="Contact", border_radius=8, expand=True)
        self.address_field = ft.TextField(label="Address", border_radius=8, expand=True)
        self.dues_field = ft.TextField(label="Outstanding Dues (Rs.)", value="0", border_radius=8, width=200, keyboard_type=ft.KeyboardType.NUMBER)

        self.editing_id = None  # Track if we're editing
        self.save_btn = ft.ElevatedButton(
            "Add Supplier",
            icon=ft.Icons.SAVE,
            on_click=self._save,
            style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_700, color=ft.Colors.WHITE, shape=ft.RoundedRectangleBorder(radius=8)),
        )
        self.cancel_btn = ft.OutlinedButton(
            "Cancel",
            on_click=self._cancel_edit,
            visible=False,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
        )
        self.status_text = ft.Text("", size=13)

        self.suppliers_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Name", weight=ft.FontWeight.W_600, size=12)),
                ft.DataColumn(ft.Text("Contact", weight=ft.FontWeight.W_600, size=12)),
                ft.DataColumn(ft.Text("Address", weight=ft.FontWeight.W_600, size=12)),
                ft.DataColumn(ft.Text("Dues (Rs.)", weight=ft.FontWeight.W_600, size=12), numeric=True),
                ft.DataColumn(ft.Text("Actions", weight=ft.FontWeight.W_600, size=12)),
            ],
            rows=[],
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=8,
            heading_row_color=ft.Colors.with_opacity(0.05, ft.Colors.BLACK),
            column_spacing=20,
        )

    def did_mount(self):
        self._load_data()

    def _load_data(self):
        suppliers = get_all_suppliers()
        rows = []
        for s in suppliers:
            rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(s["name"], size=12)),
                ft.DataCell(ft.Text(s.get("contact", ""), size=12)),
                ft.DataCell(ft.Text(s.get("address", ""), size=12)),
                ft.DataCell(ft.Text(f"Rs. {s.get('dues', 0):.2f}", size=12)),
                ft.DataCell(ft.Row([
                    ft.IconButton(ft.Icons.EDIT, icon_size=18, icon_color=ft.Colors.BLUE_600, data=s, on_click=self._start_edit, tooltip="Edit"),
                    ft.IconButton(ft.Icons.DELETE, icon_size=18, icon_color=ft.Colors.RED_600, data=s, on_click=self._delete, tooltip="Delete"),
                ], spacing=0)),
            ]))
        self.suppliers_table.rows = rows
        self._build_controls()
        self.update()

    def _build_controls(self):
        form_card = ft.Container(
            content=ft.Column([
                ft.Text("Add / Edit Supplier", size=18, weight=ft.FontWeight.BOLD),
                ft.Row([self.name_field, self.contact_field], spacing=12),
                ft.Row([self.address_field, self.dues_field], spacing=12),
                ft.Row([self.save_btn, self.cancel_btn, self.status_text], spacing=12),
            ], spacing=12),
            padding=20,
            border_radius=12,
            bgcolor=ft.Colors.WHITE,
            shadow=ft.BoxShadow(spread_radius=0, blur_radius=8, color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK), offset=ft.Offset(0, 2)),
        )

        list_card = ft.Container(
            content=ft.Column([
                ft.Text("All Suppliers", size=18, weight=ft.FontWeight.BOLD),
                self.suppliers_table,
            ], spacing=8),
            padding=20,
            border_radius=12,
            bgcolor=ft.Colors.WHITE,
            shadow=ft.BoxShadow(spread_radius=0, blur_radius=8, color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK), offset=ft.Offset(0, 2)),
        )

        self.controls = [
            ft.Container(
                content=ft.Column([
                    ft.Text("Suppliers", size=28, weight=ft.FontWeight.BOLD),
                    form_card,
                    list_card,
                ], spacing=20),
                padding=24,
            )
        ]

    def _save(self, e):
        name = self.name_field.value.strip()
        if not name:
            self.status_text.value = "❌ Name is required."
            self.status_text.color = ft.Colors.RED_700
            self.status_text.update()
            return

        contact = self.contact_field.value.strip()
        address = self.address_field.value.strip()
        try:
            dues = float(self.dues_field.value or 0)
        except ValueError:
            dues = 0.0

        if self.editing_id:
            update_supplier(self.editing_id, name, contact, address, dues)
            self.status_text.value = f"✅ Supplier '{name}' updated."
            self.editing_id = None
            self.save_btn.text = "Add Supplier"
            self.cancel_btn.visible = False
        else:
            add_supplier(name, contact, address, dues)
            self.status_text.value = f"✅ Supplier '{name}' added."

        self.status_text.color = ft.Colors.GREEN_700
        self._clear_fields()
        self._load_data()

    def _start_edit(self, e):
        s = e.control.data
        self.editing_id = s["id"]
        self.name_field.value = s["name"]
        self.contact_field.value = s.get("contact", "")
        self.address_field.value = s.get("address", "")
        self.dues_field.value = str(s.get("dues", 0))
        self.save_btn.text = "Update Supplier"
        self.cancel_btn.visible = True
        self.update()

    def _cancel_edit(self, e):
        self.editing_id = None
        self.save_btn.text = "Add Supplier"
        self.cancel_btn.visible = False
        self._clear_fields()
        self.update()

    def _delete(self, e):
        s = e.control.data

        def do_delete(ev):
            delete_supplier(s["id"])
            self.status_text.value = f"✅ Supplier '{s['name']}' deleted."
            self.status_text.color = ft.Colors.GREEN_700
            dlg.open = False
            self._page_ref.update()
            self._load_data()

        def cancel_delete(ev):
            dlg.open = False
            self._page_ref.update()

        dlg = ft.AlertDialog(
            title=ft.Text("Confirm Delete"),
            content=ft.Text(f"Delete supplier '{s['name']}'? This cannot be undone."),
            actions=[
                ft.TextButton("Cancel", on_click=cancel_delete),
                ft.TextButton("Delete", on_click=do_delete, style=ft.ButtonStyle(color=ft.Colors.RED_600)),
            ],
        )
        self._page_ref.overlay.append(dlg)
        dlg.open = True
        self._page_ref.update()

    def _clear_fields(self):
        self.name_field.value = ""
        self.contact_field.value = ""
        self.address_field.value = ""
        self.dues_field.value = "0"
