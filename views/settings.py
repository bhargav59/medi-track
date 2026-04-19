"""
views/settings.py — Shop Settings
====================================
Features:
  • Set shop name, address, phone, email, PAN (displayed on bills).
  • Set bank details (displayed on bill footer).
  • Upload shop logo (displayed on printed bills).
  
Compatible with flet 0.82+ (async FilePicker, page.services).
"""

import flet as ft
import os
import shutil
from db_manager import get_shop_settings, save_shop_settings


# Directory to store uploaded assets (alongside the database)
ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "shop_assets")


class SettingsView(ft.Column):
    """Settings view for shop branding."""

    def __init__(self, page: ft.Page):
        super().__init__()
        self._page_ref = page
        self.expand = True
        self.scroll = ft.ScrollMode.AUTO
        self.spacing = 20

        # Shop detail fields
        self.shop_name_field = ft.TextField(label="Shop Name", hint_text="e.g. Medi World Pharma Pvt. Ltd.", border_radius=8, expand=True)
        self.shop_address_field = ft.TextField(label="Address / Location", hint_text="e.g. Chhetrapath, Kathmandu", border_radius=8, expand=True)
        self.shop_phone_field = ft.TextField(label="Phone No.", hint_text="e.g. +977-9812345678", border_radius=8, expand=True)
        self.shop_email_field = ft.TextField(label="Email", hint_text="e.g. info@pharmacy.com", border_radius=8, expand=True)
        self.shop_pan_field = ft.TextField(label="PAN / VAT No.", hint_text="e.g. 619833862", border_radius=8, expand=True)
        self.shop_dda_field = ft.TextField(label="DDA Registration No.", hint_text="e.g. 123/45/67", border_radius=8, expand=True)
        self.bank_details_field = ft.TextField(
            label="Bank Details (shown on bill footer)",
            hint_text="e.g. Bank Name, A/C No., Branch",
            border_radius=8, expand=True, multiline=True, min_lines=2, max_lines=4,
        )

        self.logo_path_text = ft.Text("No logo uploaded", size=12, color=ft.Colors.GREY_600)
        self._current_logo_path = ""

        # FilePicker — Service in flet 0.82+
        self.file_picker = ft.FilePicker()

        self.upload_btn = ft.ElevatedButton(
            "Upload Logo", icon=ft.Icons.UPLOAD_FILE,
            on_click=self._open_file_picker,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
        )
        self.remove_logo_btn = ft.TextButton(
            "Remove Logo", icon=ft.Icons.DELETE,
            on_click=self._remove_logo,
            style=ft.ButtonStyle(color=ft.Colors.RED_600),
        )

        self.save_btn = ft.ElevatedButton(
            "Save Settings", icon=ft.Icons.SAVE,
            on_click=self._save_settings,
            style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_700, color=ft.Colors.WHITE, shape=ft.RoundedRectangleBorder(radius=8)),
        )
        self.status_text = ft.Text("", size=13)

    def did_mount(self):
        # FilePicker goes in page.services (not overlay) in flet 0.82+
        self._page_ref.services.append(self.file_picker)
        self._page_ref.update()
        self._load_settings()

    def _load_settings(self):
        """Load current shop settings from DB."""
        settings = get_shop_settings()
        self.shop_name_field.value = settings.get("shop_name", "")
        self.shop_address_field.value = settings.get("shop_address", "")
        self.shop_phone_field.value = settings.get("shop_phone", "")
        self.shop_email_field.value = settings.get("shop_email", "")
        self.shop_pan_field.value = settings.get("shop_pan", "")
        self.shop_dda_field.value = settings.get("shop_dda", "")
        self.bank_details_field.value = settings.get("bank_details", "")

        logo_path = settings.get("logo_path", "")
        self._current_logo_path = logo_path
        if logo_path and os.path.exists(logo_path):
            self.logo_path_text.value = f"✅ {os.path.basename(logo_path)}"
        else:
            self.logo_path_text.value = "No logo uploaded"
            self._current_logo_path = ""

        self._build_controls()
        self.update()

    def _build_controls(self):
        logo_icon = ft.Icon(
            ft.Icons.CHECK_CIRCLE if self._current_logo_path else ft.Icons.IMAGE,
            size=50,
            color=ft.Colors.GREEN_600 if self._current_logo_path else ft.Colors.GREY_400,
        )

        logo_card = ft.Container(
            content=ft.Column([
                ft.Text("Shop Logo", size=18, weight=ft.FontWeight.BOLD),
                ft.Divider(height=1),
                ft.Row([
                    ft.Container(
                        content=logo_icon,
                        width=120, height=120, border_radius=12,
                        bgcolor=ft.Colors.GREY_100,
                        alignment=ft.Alignment(0, 0),
                        border=ft.border.all(1, ft.Colors.GREY_300),
                    ),
                    ft.Column([
                        self.logo_path_text,
                        ft.Row([self.upload_btn, self.remove_logo_btn], spacing=8),
                        ft.Text("Supported: PNG, JPG, GIF (max 2MB)", size=11, color=ft.Colors.GREY_500),
                    ], spacing=8),
                ], spacing=20),
            ], spacing=12),
            padding=24, border_radius=12, bgcolor=ft.Colors.WHITE,
            shadow=ft.BoxShadow(spread_radius=0, blur_radius=8, color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK), offset=ft.Offset(0, 2)),
        )

        details_card = ft.Container(
            content=ft.Column([
                ft.Text("Shop Details (shown on Invoice header)", size=18, weight=ft.FontWeight.BOLD),
                ft.Divider(height=1),
                self.shop_name_field,
                self.shop_address_field,
                ft.Row([self.shop_phone_field, self.shop_email_field], spacing=12),
                ft.Row([self.shop_pan_field, self.shop_dda_field], spacing=12),
            ], spacing=12),
            padding=24, border_radius=12, bgcolor=ft.Colors.WHITE,
            shadow=ft.BoxShadow(spread_radius=0, blur_radius=8, color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK), offset=ft.Offset(0, 2)),
        )

        bank_card = ft.Container(
            content=ft.Column([
                ft.Text("Bank Details (shown on Invoice footer)", size=18, weight=ft.FontWeight.BOLD),
                ft.Divider(height=1),
                self.bank_details_field,
            ], spacing=12),
            padding=24, border_radius=12, bgcolor=ft.Colors.WHITE,
            shadow=ft.BoxShadow(spread_radius=0, blur_radius=8, color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK), offset=ft.Offset(0, 2)),
        )

        self.controls = [
            ft.Container(
                content=ft.Column([
                    ft.Text("Settings", size=28, weight=ft.FontWeight.BOLD),
                    details_card,
                    logo_card,
                    bank_card,
                    ft.Row([self.save_btn, self.status_text], spacing=12),
                ], spacing=20),
                padding=24,
            )
        ]

    async def _open_file_picker(self, e):
        """Open file picker — flet 0.82+ async API returns files directly."""
        try:
            files = await self.file_picker.pick_files(
                allow_multiple=False,
                allowed_extensions=["png", "jpg", "jpeg", "gif"],
                dialog_title="Select Shop Logo",
            )
        except Exception as ex:
            self.status_text.value = f"❌ File picker error: {ex}"
            self.status_text.color = ft.Colors.RED_700
            self.status_text.update()
            return

        if not files or len(files) == 0:
            return

        file = files[0]
        src_path = file.path

        if not src_path or not os.path.exists(src_path):
            self.status_text.value = "❌ Could not access the selected file."
            self.status_text.color = ft.Colors.RED_700
            self.status_text.update()
            return

        if os.path.getsize(src_path) > 2 * 1024 * 1024:
            self.status_text.value = "❌ Logo file must be under 2MB."
            self.status_text.color = ft.Colors.RED_700
            self.status_text.update()
            return

        os.makedirs(ASSETS_DIR, exist_ok=True)
        ext = os.path.splitext(file.name)[1]
        dest_path = os.path.join(ASSETS_DIR, f"shop_logo{ext}")

        try:
            shutil.copy2(src_path, dest_path)
            self._current_logo_path = dest_path
            self.logo_path_text.value = f"✅ {file.name}"
            self.status_text.value = "✅ Logo uploaded. Click 'Save Settings' to apply."
            self.status_text.color = ft.Colors.GREEN_700
        except Exception as ex:
            self.status_text.value = f"❌ Error copying logo: {ex}"
            self.status_text.color = ft.Colors.RED_700

        self._build_controls()
        self.update()

    def _remove_logo(self, e):
        self._current_logo_path = ""
        self.logo_path_text.value = "No logo uploaded"
        self.status_text.value = "Logo removed. Click 'Save Settings' to apply."
        self.status_text.color = ft.Colors.ORANGE_700
        self._build_controls()
        self.update()

    def _save_settings(self, e):
        shop_name = self.shop_name_field.value.strip()
        if not shop_name:
            self.status_text.value = "❌ Shop name cannot be empty."
            self.status_text.color = ft.Colors.RED_700
            self.status_text.update()
            return

        save_shop_settings(
            shop_name=shop_name,
            logo_path=self._current_logo_path,
            shop_address=self.shop_address_field.value.strip(),
            shop_phone=self.shop_phone_field.value.strip(),
            shop_email=self.shop_email_field.value,
            shop_pan=self.shop_pan_field.value,
            bank_details=self.bank_details_field.value,
            shop_dda=self.shop_dda_field.value
        )
        self.status_text.value = "✅ Settings saved successfully!"
        self.status_text.color = ft.Colors.GREEN_700
        self.update()
        self._page_ref.update()
