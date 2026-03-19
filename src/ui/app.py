from __future__ import annotations

import asyncio

import flet as ft

from core.capabilities import (
    FEATURE_BADUSB,
    FEATURE_INFRARED,
    FEATURE_MACROS,
    FEATURE_NFC_RFID,
    FEATURE_REMOTE,
    FEATURE_STORAGE,
    FEATURE_SUBGHZ,
    FEATURE_SYSTEM,
    build_capabilities,
)
from core.connection_manager import scan_flipper_ports
from core.flipper_api import FlipperAPI
from core.serial_client import SerialClient
from persistence.config_store import ConfigStore


def run(page: ft.Page) -> None:
    app_name = "Flipper Zero Desktop Remote"
    page.title = app_name
    page.scroll = ft.ScrollMode.AUTO
    page.padding = 20
    page.window_width = 1240
    page.window_height = 860

    serial_client = SerialClient()
    api = FlipperAPI(serial_client.send_command)
    config_store = ConfigStore(app_name)
    settings = config_store.load_settings()
    macros = config_store.load_macros()

    module_order = [
        "System",
        "Remote",
        "Storage",
        "Infrared",
        "NFC/RFID",
        "Sub-GHz",
        "BadUSB",
        "Makros",
    ]
    module_to_feature = {
        "System": FEATURE_SYSTEM,
        "Remote": FEATURE_REMOTE,
        "Storage": FEATURE_STORAGE,
        "Infrared": FEATURE_INFRARED,
        "NFC/RFID": FEATURE_NFC_RFID,
        "Sub-GHz": FEATURE_SUBGHZ,
        "BadUSB": FEATURE_BADUSB,
        "Makros": FEATURE_MACROS,
    }

    log_lines: list[str] = []
    max_log_lines = 2000
    selected_module = str(settings.get("start_module", "System"))
    if selected_module not in module_order:
        selected_module = "System"

    def accent_color() -> str:
        mapping = {
            "orange": ft.Colors.ORANGE_400,
            "amber": ft.Colors.AMBER_400,
            "red": ft.Colors.RED_400,
        }
        return mapping.get(str(settings.get("accent", "orange")), ft.Colors.ORANGE_400)

    def muted_color() -> str:
        return ft.Colors.GREY_400

    def density_value() -> str:
        value = str(settings.get("density", "comfort"))
        return value if value in {"comfort", "compact"} else "comfort"

    def spacing_value() -> int:
        return 12 if density_value() == "comfort" else 8

    def control_height() -> int:
        return 44 if density_value() == "comfort" else 36

    def apply_theme() -> None:
        mode = str(settings.get("theme", "dark"))
        page.theme_mode = ft.ThemeMode.DARK if mode == "dark" else ft.ThemeMode.LIGHT

    capabilities = build_capabilities(bool(settings.get("expert_mode", False)))
    apply_theme()

    header = ft.Text(app_name, size=30, weight=ft.FontWeight.BOLD)
    subtitle = ft.Text(
        "Steuere Flipper-Module am Desktop über klare Aktionen statt Menü-Navigation.",
        color=muted_color(),
    )

    status_chip = ft.Container(
        content=ft.Text("Nicht verbunden", color=ft.Colors.WHITE),
        bgcolor=ft.Colors.RED_700,
        padding=8,
        border_radius=10,
    )

    port_dropdown = ft.Dropdown(label="Flipper Port", width=420, options=[])
    expert_mode_checkbox = ft.Checkbox(
        label="Expert-Mode (NFC/Sub-GHz/BadUSB freischalten)",
        value=bool(settings.get("expert_mode", False)),
    )
    theme_dropdown = ft.Dropdown(
        label="Theme",
        width=180,
        value=str(settings.get("theme", "dark")),
        options=[ft.dropdown.Option("dark"), ft.dropdown.Option("light")],
    )
    accent_dropdown = ft.Dropdown(
        label="Accent",
        width=180,
        value=str(settings.get("accent", "orange")),
        options=[ft.dropdown.Option("orange"), ft.dropdown.Option("amber"), ft.dropdown.Option("red")],
    )
    density_dropdown = ft.Dropdown(
        label="Dichte",
        width=180,
        value=density_value(),
        options=[ft.dropdown.Option("comfort"), ft.dropdown.Option("compact")],
    )
    start_module_dropdown = ft.Dropdown(
        label="Startmodul",
        width=220,
        value=selected_module,
        options=[ft.dropdown.Option(m) for m in module_order],
    )

    raw_cmd_input = ft.TextField(label="Raw CLI", hint_text="Befehl eingeben", expand=True)

    log_console = ft.TextField(
        label="Debug Log",
        multiline=True,
        min_lines=12,
        max_lines=12,
        read_only=True,
        value="",
    )
    mini_log_console = ft.TextField(
        label="Letzte Logs",
        multiline=True,
        min_lines=6,
        max_lines=6,
        read_only=True,
        value="",
    )

    system_path_input = ft.TextField(label="Storage Pfad", value="/", width=320)
    storage_list_path_input = ft.TextField(label="Listen-Pfad", value="/", width=320)
    storage_upload_local = ft.TextField(label="Lokale Datei", value="", width=340)
    storage_upload_remote = ft.TextField(label="Ziel auf Flipper", value="/ext/", width=280)
    storage_download_remote = ft.TextField(label="Quelle auf Flipper", value="/ext/", width=280)
    storage_download_local = ft.TextField(label="Lokaler Zielpfad", value="", width=340)

    ir_command_input = ft.TextField(label="IR CLI", value="ir tx /ext/infrared/example.ir", expand=True)
    nfc_command_input = ft.TextField(label="NFC/RFID CLI", value="nfc detect", expand=True)
    subghz_command_input = ft.TextField(label="Sub-GHz CLI", value="subghz rx", expand=True)
    badusb_command_input = ft.TextField(label="BadUSB CLI", value="badusb run /ext/badusb/script.txt", expand=True)
    badusb_confirm = ft.Checkbox(label="Ich bestätige kontrollierte/legitime Nutzung", value=False)

    macro_select = ft.Dropdown(label="Gespeichertes Makro", width=280, options=[])
    macro_name_input = ft.TextField(label="Makro-Name", width=280)
    macro_commands_input = ft.TextField(
        label="Makro-Befehle (eine Zeile = ein Befehl)",
        multiline=True,
        min_lines=7,
        max_lines=9,
    )

    main_tabs = ft.Tabs(
        content=ft.Row([ft.Tab(label="Home"), ft.Tab(label="Module"), ft.Tab(label="Settings")]),
        length=3,
        selected_index=0,
        animation_duration=150,
    )
    module_tabs = ft.Tabs(
        content=ft.Row([ft.Tab(label=name) for name in module_order]),
        length=len(module_order),
        selected_index=module_order.index(selected_module),
        animation_duration=120,
    )

    main_content = ft.Container(expand=True)
    module_panel_content = ft.Container(expand=True)

    def update_log_views() -> None:
        log_console.value = "\n".join(log_lines)
        mini_log_console.value = "\n".join(log_lines[-60:])

    def append_log(line: str) -> None:
        log_lines.append(line)
        if len(log_lines) > max_log_lines:
            del log_lines[: len(log_lines) - max_log_lines]
        update_log_views()

    def update_connection_status() -> None:
        if serial_client.is_connected:
            status_chip.content = ft.Text("Verbunden", color=ft.Colors.WHITE)
            status_chip.bgcolor = ft.Colors.GREEN_700
        else:
            status_chip.content = ft.Text("Nicht verbunden", color=ft.Colors.WHITE)
            status_chip.bgcolor = ft.Colors.RED_700

    def panel_card(title: str, subtitle_text: str, body: list[ft.Control]) -> ft.Control:
        return ft.Container(
            padding=14,
            border_radius=14,
            border=ft.border.all(1, ft.Colors.with_opacity(0.24, accent_color())),
            bgcolor=ft.Colors.with_opacity(0.06, accent_color()),
            content=ft.Column(
                spacing=spacing_value(),
                controls=[
                    ft.Text(title, size=19, weight=ft.FontWeight.BOLD),
                    ft.Text(subtitle_text, color=muted_color()),
                    *body,
                ],
            ),
        )

    def is_enabled(feature_key: str) -> bool:
        capability = capabilities.get(feature_key)
        return bool(capability and capability.enabled)

    def feature_hint(feature_key: str) -> str:
        capability = capabilities.get(feature_key)
        return capability.hint if capability else "Feature-Zustand unbekannt"

    def switch_to_settings(_: ft.ControlEvent) -> None:
        main_tabs.selected_index = 2
        refresh_main_view()
        page.update()

    def disabled_feature_panel(module_name: str, feature_key: str) -> ft.Control:
        return panel_card(
            f"{module_name} deaktiviert",
            feature_hint(feature_key),
            [
                ft.Text("Aktiviere den Expert-Mode in Settings, falls du dieses Modul nutzen willst."),
                ft.OutlinedButton("Zu Settings", on_click=switch_to_settings, height=control_height()),
            ],
        )

    def guarded_call(feature_key: str, callback) -> None:
        if not is_enabled(feature_key):
            append_log(f"[INFO] {feature_hint(feature_key)}")
            return
        if not serial_client.is_connected:
            append_log("[WARN] Kein Flipper verbunden")
            return
        try:
            callback()
        except Exception as exc:
            append_log(f"[ERROR] {exc}")

    def run_command(command: str) -> None:
        clean = command.strip()
        if not clean:
            return
        guarded_call(FEATURE_SYSTEM, lambda: api.raw(clean))

    def perform_scan() -> None:
        ports = scan_flipper_ports()
        port_dropdown.options = [ft.dropdown.Option(port) for port in ports]
        last_port = str(settings.get("last_port", ""))
        if last_port and last_port in ports:
            port_dropdown.value = last_port
        elif ports and not port_dropdown.value:
            port_dropdown.value = ports[0]

        if ports:
            append_log(f"[INFO] Gefundene Ports: {', '.join(ports)}")
        else:
            append_log("[WARN] Keine passenden Flipper-Ports gefunden")

    def connect_selected_port() -> None:
        selected_port = (port_dropdown.value or "").strip()
        if not selected_port:
            append_log("[WARN] Bitte zuerst einen Port auswählen")
            return
        try:
            serial_client.connect(selected_port)
            settings["last_port"] = selected_port
            config_store.save_settings(settings)
            append_log(f"[INFO] Verbindung hergestellt: {selected_port}")
        except Exception as exc:
            append_log(f"[ERROR] Verbindung fehlgeschlagen: {exc}")
        update_connection_status()

    def disconnect() -> None:
        serial_client.disconnect()
        update_connection_status()

    def refresh_macro_dropdown() -> None:
        macro_select.options = [ft.dropdown.Option(name) for name in sorted(macros.keys())]
        if macro_select.value not in macros and macro_select.options:
            macro_select.value = macro_select.options[0].key

    def load_selected_macro(_: ft.ControlEvent) -> None:
        selected_name = (macro_select.value or "").strip()
        if selected_name and selected_name in macros:
            macro_name_input.value = selected_name
            macro_commands_input.value = "\n".join(macros[selected_name])
            page.update()

    def save_macro(_: ft.ControlEvent) -> None:
        name = (macro_name_input.value or "").strip()
        commands = [line.strip() for line in (macro_commands_input.value or "").splitlines() if line.strip()]
        if not name:
            append_log("[WARN] Makro-Name fehlt")
            page.update()
            return
        if not commands:
            append_log("[WARN] Makro enthält keine Befehle")
            page.update()
            return

        macros[name] = commands
        config_store.save_macros(macros)
        refresh_macro_dropdown()
        macro_select.value = name
        append_log(f"[INFO] Makro gespeichert: {name}")
        page.update()

    def delete_macro(_: ft.ControlEvent) -> None:
        selected = (macro_select.value or "").strip()
        if not selected:
            append_log("[WARN] Kein Makro ausgewählt")
            page.update()
            return

        if selected in macros:
            del macros[selected]
            config_store.save_macros(macros)
            refresh_macro_dropdown()
            if macros:
                next_name = sorted(macros.keys())[0]
                macro_select.value = next_name
                macro_name_input.value = next_name
                macro_commands_input.value = "\n".join(macros[next_name])
            else:
                macro_select.value = None
                macro_name_input.value = ""
                macro_commands_input.value = ""
            append_log(f"[INFO] Makro gelöscht: {selected}")
        page.update()

    def run_macro(_: ft.ControlEvent) -> None:
        selected = (macro_select.value or "").strip()
        if not selected:
            append_log("[WARN] Kein Makro ausgewählt")
            page.update()
            return

        commands = macros.get(selected, [])
        if not commands:
            append_log("[WARN] Makro ist leer")
            page.update()
            return

        def execute() -> None:
            for command in commands:
                api.raw(command)

        guarded_call(FEATURE_MACROS, execute)
        append_log(f"[INFO] Makro gestartet: {selected} ({len(commands)} Befehle)")
        page.update()

    def module_card(module_name: str, icon: ft.IconData) -> ft.Control:
        feature_key = module_to_feature[module_name]
        enabled = is_enabled(feature_key)
        status = "Aktiv" if enabled else "Deaktiviert"
        status_color = ft.Colors.GREEN_400 if enabled else ft.Colors.GREY_500

        def open_module(_: ft.ControlEvent) -> None:
            nonlocal selected_module
            selected_module = module_name
            module_tabs.selected_index = module_order.index(module_name)
            main_tabs.selected_index = 1
            settings["start_module"] = module_name
            start_module_dropdown.value = module_name
            config_store.save_settings(settings)
            refresh_main_view()
            page.update()

        return ft.ElevatedButton(
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=6,
                controls=[
                    ft.Icon(icon, size=24, color=accent_color() if enabled else ft.Colors.GREY_500),
                    ft.Text(module_name, weight=ft.FontWeight.W_600),
                    ft.Text(status, color=status_color, size=12),
                ],
            ),
            height=115 if density_value() == "comfort" else 100,
            width=210,
            on_click=open_module,
        )

    def build_home_view() -> ft.Control:
        cards = [
            module_card("System", ft.Icons.DEVELOPER_MODE),
            module_card("Remote", ft.Icons.GAMEPAD_ROUNDED),
            module_card("Storage", ft.Icons.FOLDER_ROUNDED),
            module_card("Infrared", ft.Icons.SETTINGS_REMOTE_ROUNDED),
            module_card("NFC/RFID", ft.Icons.NFC_ROUNDED),
            module_card("Sub-GHz", ft.Icons.NETWORK_CELL_ROUNDED),
            module_card("BadUSB", ft.Icons.USB_ROUNDED),
            module_card("Makros", ft.Icons.AUTO_MODE_ROUNDED),
        ]

        quick_actions = panel_card(
            "Quick Actions",
            "Schnellbefehle direkt vom Dashboard.",
            [
                ft.Row(
                    wrap=True,
                    spacing=8,
                    run_spacing=8,
                    controls=[
                        ft.ElevatedButton(
                            "Device Info",
                            on_click=lambda _: (guarded_call(FEATURE_SYSTEM, api.device_info), page.update()),
                            height=control_height(),
                        ),
                        ft.OutlinedButton(
                            "Vibro Test",
                            on_click=lambda _: (
                                guarded_call(FEATURE_SYSTEM, lambda: api.vibro(True)),
                                guarded_call(FEATURE_SYSTEM, lambda: api.vibro(False)),
                                page.update(),
                            ),
                            height=control_height(),
                        ),
                        ft.OutlinedButton(
                            "Storage /",
                            on_click=lambda _: (guarded_call(FEATURE_STORAGE, lambda: api.storage_list("/")), page.update()),
                            height=control_height(),
                        ),
                        ft.OutlinedButton(
                            "Reboot",
                            on_click=lambda _: (guarded_call(FEATURE_SYSTEM, api.reboot_normal), page.update()),
                            height=control_height(),
                        ),
                    ],
                )
            ],
        )

        favorites = panel_card(
            "Favoriten",
            "Häufig genutzte Aktionen als direkte Launcher.",
            [
                ft.Row(
                    wrap=True,
                    spacing=8,
                    run_spacing=8,
                    controls=[
                        ft.ElevatedButton(
                            "OK short",
                            on_click=lambda _: (guarded_call(FEATURE_REMOTE, lambda: api.input_send("ok", "short")), page.update()),
                            height=control_height(),
                        ),
                        ft.OutlinedButton(
                            "Back",
                            on_click=lambda _: (guarded_call(FEATURE_REMOTE, lambda: api.input_send("back", "short")), page.update()),
                            height=control_height(),
                        ),
                        ft.OutlinedButton(
                            "Macro: Status",
                            on_click=lambda _: (
                                macro_select.__setattr__("value", "Status" if "Status" in macros else macro_select.value),
                                run_macro(_),
                            ),
                            height=control_height(),
                        ),
                    ],
                )
            ],
        )

        log_card = panel_card("Mini Log", "Live-Output für schnellen Überblick.", [mini_log_console])

        return ft.Column(
            spacing=spacing_value(),
            controls=[
                ft.Text("Dashboard", size=23, weight=ft.FontWeight.BOLD),
                ft.Text("Wähle ein Modul über Kacheln oder nutze direkte Schnellaktionen.", color=muted_color()),
                ft.Row(wrap=True, spacing=10, run_spacing=10, controls=cards),
                quick_actions,
                favorites,
                log_card,
            ],
        )

    def build_system_module() -> ft.Control:
        return panel_card(
            "System & Diagnose",
            feature_hint(FEATURE_SYSTEM),
            [
                ft.Row(
                    wrap=True,
                    spacing=8,
                    run_spacing=8,
                    controls=[
                        ft.ElevatedButton(
                            "Device Info",
                            on_click=lambda _: (guarded_call(FEATURE_SYSTEM, api.device_info), page.update()),
                            height=control_height(),
                        ),
                        ft.OutlinedButton(
                            "Storage Pfad listen",
                            on_click=lambda _: (
                                guarded_call(FEATURE_STORAGE, lambda: api.storage_list(system_path_input.value or "/")),
                                page.update(),
                            ),
                            height=control_height(),
                        ),
                    ],
                ),
                system_path_input,
            ],
        )

    def build_remote_module() -> ft.Control:
        short_buttons = {
            "↑": "up",
            "↓": "down",
            "←": "left",
            "→": "right",
            "OK": "ok",
            "Back": "back",
        }
        long_buttons = {
            "↑ long": "up",
            "↓ long": "down",
            "← long": "left",
            "→ long": "right",
            "OK long": "ok",
            "Back long": "back",
        }

        return panel_card(
            "Remote Control",
            feature_hint(FEATURE_REMOTE),
            [
                ft.Row(
                    wrap=True,
                    spacing=8,
                    run_spacing=8,
                    controls=[
                        ft.ElevatedButton(
                            label,
                            on_click=lambda _, key_name=key: (
                                guarded_call(FEATURE_REMOTE, lambda: api.input_send(key_name, "short")),
                                page.update(),
                            ),
                            height=control_height(),
                        )
                        for label, key in short_buttons.items()
                    ],
                ),
                ft.Row(
                    wrap=True,
                    spacing=8,
                    run_spacing=8,
                    controls=[
                        ft.OutlinedButton(
                            label,
                            on_click=lambda _, key_name=key: (
                                guarded_call(FEATURE_REMOTE, lambda: api.input_long_with_fallback(key_name)),
                                page.update(),
                            ),
                            height=control_height(),
                        )
                        for label, key in long_buttons.items()
                    ],
                ),
            ],
        )

    def build_storage_module() -> ft.Control:
        return panel_card(
            "Storage",
            feature_hint(FEATURE_STORAGE),
            [
                ft.Row(
                    wrap=True,
                    spacing=8,
                    run_spacing=8,
                    controls=[
                        storage_list_path_input,
                        ft.ElevatedButton(
                            "List",
                            on_click=lambda _: (
                                guarded_call(FEATURE_STORAGE, lambda: api.storage_list(storage_list_path_input.value or "/")),
                                page.update(),
                            ),
                            height=control_height(),
                        ),
                    ],
                ),
                ft.Row(
                    wrap=True,
                    spacing=8,
                    run_spacing=8,
                    controls=[
                        storage_upload_local,
                        storage_upload_remote,
                        ft.OutlinedButton(
                            "Upload (Template)",
                            on_click=lambda _: (
                                run_command(
                                    f"storage write {storage_upload_local.value.strip()} {storage_upload_remote.value.strip()}"
                                ),
                                page.update(),
                            ),
                            height=control_height(),
                        ),
                    ],
                ),
                ft.Row(
                    wrap=True,
                    spacing=8,
                    run_spacing=8,
                    controls=[
                        storage_download_remote,
                        storage_download_local,
                        ft.OutlinedButton(
                            "Download (Template)",
                            on_click=lambda _: (
                                run_command(
                                    f"storage read {storage_download_remote.value.strip()} {storage_download_local.value.strip()}"
                                ),
                                page.update(),
                            ),
                            height=control_height(),
                        ),
                    ],
                ),
            ],
        )

    def build_infrared_module() -> ft.Control:
        return panel_card(
            "Infrared",
            feature_hint(FEATURE_INFRARED),
            [
                ir_command_input,
                ft.Row(
                    wrap=True,
                    spacing=8,
                    run_spacing=8,
                    controls=[
                        ft.ElevatedButton(
                            "Ausführen",
                            on_click=lambda _: (guarded_call(FEATURE_INFRARED, lambda: api.raw(ir_command_input.value)), page.update()),
                            height=control_height(),
                        ),
                        ft.OutlinedButton(
                            "Template: Send",
                            on_click=lambda _: (setattr(ir_command_input, "value", "ir tx /ext/infrared/example.ir"), page.update()),
                            height=control_height(),
                        ),
                        ft.OutlinedButton(
                            "Template: Learn",
                            on_click=lambda _: (setattr(ir_command_input, "value", "ir rx"), page.update()),
                            height=control_height(),
                        ),
                    ],
                ),
            ],
        )

    def build_nfc_module() -> ft.Control:
        return panel_card(
            "NFC/RFID",
            feature_hint(FEATURE_NFC_RFID),
            [
                nfc_command_input,
                ft.Row(
                    wrap=True,
                    spacing=8,
                    run_spacing=8,
                    controls=[
                        ft.ElevatedButton(
                            "Ausführen",
                            on_click=lambda _: (guarded_call(FEATURE_NFC_RFID, lambda: api.raw(nfc_command_input.value)), page.update()),
                            height=control_height(),
                        ),
                        ft.OutlinedButton(
                            "Detect",
                            on_click=lambda _: (setattr(nfc_command_input, "value", "nfc detect"), page.update()),
                            height=control_height(),
                        ),
                        ft.OutlinedButton(
                            "Read",
                            on_click=lambda _: (setattr(nfc_command_input, "value", "nfc read"), page.update()),
                            height=control_height(),
                        ),
                    ],
                ),
            ],
        )

    def build_subghz_module() -> ft.Control:
        return panel_card(
            "Sub-GHz",
            feature_hint(FEATURE_SUBGHZ),
            [
                subghz_command_input,
                ft.Row(
                    wrap=True,
                    spacing=8,
                    run_spacing=8,
                    controls=[
                        ft.ElevatedButton(
                            "Ausführen",
                            on_click=lambda _: (guarded_call(FEATURE_SUBGHZ, lambda: api.raw(subghz_command_input.value)), page.update()),
                            height=control_height(),
                        ),
                        ft.OutlinedButton(
                            "RX",
                            on_click=lambda _: (setattr(subghz_command_input, "value", "subghz rx"), page.update()),
                            height=control_height(),
                        ),
                        ft.OutlinedButton(
                            "TX",
                            on_click=lambda _: (setattr(subghz_command_input, "value", "subghz tx"), page.update()),
                            height=control_height(),
                        ),
                    ],
                ),
                ft.Text("Nur auf legalen Frequenzen nutzen.", color=ft.Colors.RED_300),
            ],
        )

    def build_badusb_module() -> ft.Control:
        return panel_card(
            "BadUSB",
            feature_hint(FEATURE_BADUSB),
            [
                badusb_command_input,
                badusb_confirm,
                ft.ElevatedButton(
                    "Ausführen",
                    on_click=lambda _: (
                        append_log("[WARN] Bestätigung fehlt")
                        if not badusb_confirm.value
                        else guarded_call(FEATURE_BADUSB, lambda: api.raw(badusb_command_input.value)),
                        page.update(),
                    ),
                    height=control_height(),
                ),
            ],
        )

    def build_macros_module() -> ft.Control:
        return panel_card(
            "Makros",
            feature_hint(FEATURE_MACROS),
            [
                ft.Row(wrap=True, spacing=8, controls=[macro_select, ft.OutlinedButton("Laden", on_click=load_selected_macro)]),
                macro_name_input,
                macro_commands_input,
                ft.Row(
                    wrap=True,
                    spacing=8,
                    run_spacing=8,
                    controls=[
                        ft.ElevatedButton("Speichern", on_click=save_macro, height=control_height()),
                        ft.OutlinedButton("Löschen", on_click=delete_macro, height=control_height()),
                        ft.OutlinedButton("Ausführen", on_click=run_macro, height=control_height()),
                    ],
                ),
            ],
        )

    def rebuild_module_panel() -> None:
        feature_key = module_to_feature[selected_module]
        if not is_enabled(feature_key):
            module_panel_content.content = disabled_feature_panel(selected_module, feature_key)
            return

        if selected_module == "System":
            module_panel_content.content = build_system_module()
        elif selected_module == "Remote":
            module_panel_content.content = build_remote_module()
        elif selected_module == "Storage":
            module_panel_content.content = build_storage_module()
        elif selected_module == "Infrared":
            module_panel_content.content = build_infrared_module()
        elif selected_module == "NFC/RFID":
            module_panel_content.content = build_nfc_module()
        elif selected_module == "Sub-GHz":
            module_panel_content.content = build_subghz_module()
        elif selected_module == "BadUSB":
            module_panel_content.content = build_badusb_module()
        else:
            module_panel_content.content = build_macros_module()

    def build_module_view() -> ft.Control:
        return ft.Column(
            spacing=spacing_value(),
            controls=[
                ft.Text(f"Modul: {selected_module}", size=23, weight=ft.FontWeight.BOLD),
                module_tabs,
                module_panel_content,
            ],
        )

    def on_scan(_: ft.ControlEvent) -> None:
        perform_scan()
        page.update()

    def on_connect(_: ft.ControlEvent) -> None:
        connect_selected_port()
        page.update()

    def on_disconnect(_: ft.ControlEvent) -> None:
        disconnect()
        page.update()

    def on_send_raw(_: ft.ControlEvent) -> None:
        run_command(raw_cmd_input.value or "")
        raw_cmd_input.value = ""
        page.update()

    def on_expert_mode_change(_: ft.ControlEvent) -> None:
        settings["expert_mode"] = bool(expert_mode_checkbox.value)
        config_store.save_settings(settings)
        nonlocal capabilities
        capabilities = build_capabilities(bool(settings.get("expert_mode", False)))
        append_log("[INFO] Expert-Mode aktualisiert")
        rebuild_module_panel()
        refresh_main_view()
        page.update()

    def on_theme_change(_: ft.ControlEvent) -> None:
        settings["theme"] = theme_dropdown.value or "dark"
        config_store.save_settings(settings)
        apply_theme()
        refresh_main_view()
        page.update()

    def on_accent_change(_: ft.ControlEvent) -> None:
        settings["accent"] = accent_dropdown.value or "orange"
        config_store.save_settings(settings)
        refresh_main_view()
        page.update()

    def on_density_change(_: ft.ControlEvent) -> None:
        settings["density"] = density_dropdown.value or "comfort"
        config_store.save_settings(settings)
        refresh_main_view()
        page.update()

    def on_start_module_change(_: ft.ControlEvent) -> None:
        nonlocal selected_module
        value = start_module_dropdown.value or "System"
        if value in module_order:
            selected_module = value
            settings["start_module"] = value
            module_tabs.selected_index = module_order.index(value)
            config_store.save_settings(settings)
            rebuild_module_panel()
            page.update()

    def reset_settings(_: ft.ControlEvent) -> None:
        nonlocal selected_module, capabilities
        settings.clear()
        settings.update(
            {
                "last_port": "",
                "expert_mode": False,
                "theme": "dark",
                "accent": "orange",
                "density": "comfort",
                "start_module": "System",
            }
        )
        config_store.save_settings(settings)
        capabilities = build_capabilities(False)
        selected_module = "System"
        expert_mode_checkbox.value = False
        theme_dropdown.value = "dark"
        accent_dropdown.value = "orange"
        density_dropdown.value = "comfort"
        start_module_dropdown.value = "System"
        module_tabs.selected_index = 0
        apply_theme()
        rebuild_module_panel()
        refresh_main_view()
        append_log("[INFO] Settings zurückgesetzt")
        page.update()

    def reset_macros(_: ft.ControlEvent) -> None:
        macros.clear()
        macros.update({"Status": ["device_info", "storage list /"], "Quick Reboot": ["power reboot"]})
        config_store.save_macros(macros)
        refresh_macro_dropdown()
        if "Status" in macros:
            macro_select.value = "Status"
            macro_name_input.value = "Status"
            macro_commands_input.value = "\n".join(macros["Status"])
        append_log("[INFO] Makros zurückgesetzt")
        page.update()

    def build_settings_view() -> ft.Control:
        connection_card = panel_card(
            "Verbindung",
            "USB-Port scannen und Flipper verbinden.",
            [
                ft.Row(
                    wrap=True,
                    spacing=8,
                    run_spacing=8,
                    controls=[
                        port_dropdown,
                        ft.ElevatedButton("Scan", on_click=on_scan, height=control_height()),
                        ft.ElevatedButton("Connect", on_click=on_connect, height=control_height()),
                        ft.OutlinedButton("Disconnect", on_click=on_disconnect, height=control_height()),
                        status_chip,
                    ],
                )
            ],
        )

        ui_card = panel_card(
            "UI & Sicherheit",
            "Theme, Dichte, Startmodul und Expert-Einstellungen.",
            [
                ft.Row(
                    wrap=True,
                    spacing=8,
                    run_spacing=8,
                    controls=[theme_dropdown, accent_dropdown, density_dropdown, start_module_dropdown],
                ),
                expert_mode_checkbox,
            ],
        )

        debug_card = panel_card(
            "Debug Console",
            "Raw-Befehle und vollständige Logs.",
            [
                ft.Row(
                    spacing=8,
                    controls=[
                        raw_cmd_input,
                        ft.ElevatedButton("Raw senden", on_click=on_send_raw, height=control_height()),
                        ft.OutlinedButton(
                            "Logs leeren",
                            on_click=lambda _: (log_lines.clear(), update_log_views(), page.update()),
                            height=control_height(),
                        ),
                    ],
                ),
                log_console,
            ],
        )

        danger_card = panel_card(
            "Danger Zone",
            "Setzt lokale App-Einstellungen oder Makros zurück.",
            [
                ft.Row(
                    wrap=True,
                    spacing=8,
                    run_spacing=8,
                    controls=[
                        ft.OutlinedButton("Settings reset", on_click=reset_settings, height=control_height()),
                        ft.OutlinedButton("Makros reset", on_click=reset_macros, height=control_height()),
                    ],
                )
            ],
        )

        return ft.Column(
            spacing=spacing_value(),
            controls=[
                ft.Text("Settings", size=23, weight=ft.FontWeight.BOLD),
                connection_card,
                ui_card,
                debug_card,
                danger_card,
            ],
        )

    def refresh_main_view() -> None:
        selected = main_tabs.selected_index or 0
        if selected == 0:
            main_content.content = build_home_view()
        elif selected == 1:
            rebuild_module_panel()
            main_content.content = build_module_view()
        else:
            main_content.content = build_settings_view()

    def on_main_tab_change(_: ft.ControlEvent) -> None:
        refresh_main_view()
        page.update()

    def on_module_tab_change(_: ft.ControlEvent) -> None:
        nonlocal selected_module
        idx = module_tabs.selected_index if module_tabs.selected_index is not None else 0
        selected_module = module_order[idx]
        settings["start_module"] = selected_module
        start_module_dropdown.value = selected_module
        config_store.save_settings(settings)
        rebuild_module_panel()
        refresh_main_view()
        page.update()

    main_tabs.on_change = on_main_tab_change
    module_tabs.on_change = on_module_tab_change
    expert_mode_checkbox.on_change = on_expert_mode_change
    theme_dropdown.on_change = on_theme_change
    accent_dropdown.on_change = on_accent_change
    density_dropdown.on_change = on_density_change
    start_module_dropdown.on_change = on_start_module_change

    page.add(
        ft.Column(
            spacing=spacing_value(),
            controls=[
                header,
                subtitle,
                ft.Divider(height=1, color=accent_color()),
                main_tabs,
                main_content,
            ],
        )
    )

    refresh_macro_dropdown()
    if macros:
        first_macro = sorted(macros.keys())[0]
        macro_select.value = first_macro
        macro_name_input.value = first_macro
        macro_commands_input.value = "\n".join(macros[first_macro])

    perform_scan()
    update_connection_status()
    refresh_main_view()
    page.update()

    def on_window_event(event: ft.WindowEvent) -> None:
        if event.data == "close":
            serial_client.disconnect()

    page.on_window_event = on_window_event

    async def pump_logs() -> None:
        while True:
            lines = serial_client.pop_logs()
            if lines:
                for line in lines:
                    append_log(line)
                page.update()
            await asyncio.sleep(0.2)

    page.run_task(pump_logs)
