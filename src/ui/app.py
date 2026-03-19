from __future__ import annotations

import asyncio
import time

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

    log_console = ft.TextField(
        label="Aktivitäten",
        multiline=True,
        min_lines=12,
        max_lines=12,
        read_only=True,
        value="",
    )
    mini_log_console = ft.TextField(
        label="Letzte Aktivitäten",
        multiline=True,
        min_lines=6,
        max_lines=6,
        read_only=True,
        value="",
    )

    common_path_options = ["/", "/ext", "/ext/apps", "/ext/infrared", "/ext/nfc", "/ext/subghz", "/ext/badusb"]

    system_path_input = ft.Dropdown(
        label="Ordner",
        width=320,
        value="/",
        options=[ft.dropdown.Option(path) for path in common_path_options],
    )
    storage_list_path_input = ft.Dropdown(
        label="Ordner",
        width=320,
        value="/",
        options=[ft.dropdown.Option(path) for path in common_path_options],
    )
    storage_mkdir_path = ft.Dropdown(
        label="Neuer Ordner",
        width=320,
        value="/ext/new_folder",
        options=[
            ft.dropdown.Option("/ext/new_folder"),
            ft.dropdown.Option("/ext/apps/new_folder"),
            ft.dropdown.Option("/ext/infrared/new_folder"),
        ],
    )
    storage_remove_path = ft.Dropdown(
        label="Element löschen",
        width=320,
        value="/ext/old_file.txt",
        options=[
            ft.dropdown.Option("/ext/old_file.txt"),
            ft.dropdown.Option("/ext/notes.txt"),
            ft.dropdown.Option("/ext/new_folder"),
        ],
    )
    storage_read_path = ft.Dropdown(
        label="Datei",
        width=320,
        value="/ext/notes.txt",
        options=[
            ft.dropdown.Option("/ext/notes.txt"),
            ft.dropdown.Option("/ext/infrared/example.ir"),
            ft.dropdown.Option("/ext/badusb/script.txt"),
        ],
    )

    ir_file_path = ft.Dropdown(
        label="IR-Datei",
        width=360,
        value="/ext/infrared/example.ir",
        options=[
            ft.dropdown.Option("/ext/infrared/example.ir"),
            ft.dropdown.Option("/ext/infrared/tv.ir"),
            ft.dropdown.Option("/ext/infrared/ac.ir"),
        ],
    )
    nfc_file_path = ft.Dropdown(
        label="NFC-Datei",
        width=360,
        value="/ext/nfc/example.nfc",
        options=[
            ft.dropdown.Option("/ext/nfc/example.nfc"),
            ft.dropdown.Option("/ext/nfc/card1.nfc"),
            ft.dropdown.Option("/ext/nfc/card2.nfc"),
        ],
    )
    subghz_file_path = ft.Dropdown(
        label="Funk-Datei",
        width=360,
        value="/ext/subghz/example.sub",
        options=[
            ft.dropdown.Option("/ext/subghz/example.sub"),
            ft.dropdown.Option("/ext/subghz/garage.sub"),
            ft.dropdown.Option("/ext/subghz/doorbell.sub"),
        ],
    )
    badusb_script_path = ft.Dropdown(
        label="Ablauf-Datei",
        width=360,
        value="/ext/badusb/script.txt",
        options=[
            ft.dropdown.Option("/ext/badusb/script.txt"),
            ft.dropdown.Option("/ext/badusb/test.txt"),
            ft.dropdown.Option("/ext/badusb/demo.txt"),
        ],
    )
    badusb_confirm = ft.Checkbox(label="Ich bestätige kontrollierte/legitime Nutzung", value=False)

    macro_select = ft.Dropdown(label="Gespeichertes Makro", width=280, options=[])
    macro_name_input = ft.TextField(label="Makro-Name", width=280)
    macro_commands_input = ft.TextField(
        label="Makro-Schritte (eine Zeile = ein Schritt)",
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
    scan_status_text = ft.Text("Dateien: nicht geladen", color=muted_color(), size=12)

    scan_dirs = ["/ext", "/ext/infrared", "/ext/nfc", "/ext/subghz", "/ext/badusb"]
    storage_scan_active = False
    storage_scan_current_dir = ""
    storage_scan_last_activity = 0.0
    storage_scan_paths: set[str] = set()
    ir_paths: set[str] = set()
    nfc_paths: set[str] = set()
    subghz_paths: set[str] = set()
    badusb_paths: set[str] = set()

    def notify(message: str, error: bool = False) -> None:
        page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=ft.Colors.RED_700 if error else ft.Colors.with_opacity(0.9, accent_color()),
            open=True,
        )

    def update_log_views() -> None:
        log_console.value = "\n".join(log_lines)
        mini_log_console.value = "\n".join(log_lines[-60:])

    def set_scan_status(message: str, error: bool = False) -> None:
        scan_status_text.value = message
        scan_status_text.color = ft.Colors.RED_300 if error else muted_color()

    def append_log(line: str) -> None:
        log_lines.append(line)
        if len(log_lines) > max_log_lines:
            del log_lines[: len(log_lines) - max_log_lines]
        update_log_views()

    def set_dropdown_values(dropdown: ft.Dropdown, values: set[str], fallback: str) -> None:
        merged = sorted({value for value in values if value} | {fallback})
        dropdown.options = [ft.dropdown.Option(value) for value in merged]
        if not dropdown.value or str(dropdown.value) not in merged:
            dropdown.value = merged[0]

    def apply_scanned_paths() -> None:
        if storage_scan_paths:
            set_dropdown_values(storage_remove_path, storage_scan_paths, "/ext/old_file.txt")
            set_dropdown_values(storage_read_path, storage_scan_paths, "/ext/notes.txt")

        if ir_paths:
            set_dropdown_values(ir_file_path, ir_paths, "/ext/infrared/example.ir")
        if nfc_paths:
            set_dropdown_values(nfc_file_path, nfc_paths, "/ext/nfc/example.nfc")
        if subghz_paths:
            set_dropdown_values(subghz_file_path, subghz_paths, "/ext/subghz/example.sub")
        if badusb_paths:
            set_dropdown_values(badusb_script_path, badusb_paths, "/ext/badusb/script.txt")

    def normalize_storage_path(current_dir: str, entry: str) -> str:
        value = entry.strip().strip('"').strip("'")
        if not value or value in {".", ".."}:
            return ""
        if value.startswith("/"):
            return value
        return f"{current_dir.rstrip('/')}/{value}"

    def extract_storage_entry(line: str) -> str:
        text = line.strip()
        if not text:
            return ""
        if text.startswith(">") or text.startswith("["):
            return ""
        lowered = text.lower()
        if "storage" in lowered and ("error" in lowered or "usage" in lowered):
            return ""

        tokens = text.replace("\t", " ").split()
        if not tokens:
            return ""
        candidate = tokens[-1]
        return "" if candidate in {"-", "|"} else candidate

    def process_scan_line(line: str) -> None:
        nonlocal storage_scan_current_dir, storage_scan_last_activity, storage_scan_active
        if not storage_scan_active:
            return

        storage_scan_last_activity = time.time()
        stripped = line.strip()
        if stripped.startswith("> storage list "):
            storage_scan_current_dir = stripped.replace("> storage list ", "", 1).strip() or "/"
            return
        if stripped.startswith(">"):
            return
        if not storage_scan_current_dir:
            return

        entry = extract_storage_entry(stripped)
        if not entry:
            return
        full_path = normalize_storage_path(storage_scan_current_dir, entry)
        if not full_path or full_path.endswith("/"):
            return

        storage_scan_paths.add(full_path)
        lower_path = full_path.lower()
        if lower_path.endswith(".ir") or "/infrared/" in lower_path:
            ir_paths.add(full_path)
        if lower_path.endswith(".nfc") or "/nfc/" in lower_path:
            nfc_paths.add(full_path)
        if lower_path.endswith(".sub") or "/subghz/" in lower_path:
            subghz_paths.add(full_path)
        if lower_path.endswith(".txt") or "/badusb/" in lower_path:
            badusb_paths.add(full_path)

    def finish_scan_if_idle() -> None:
        nonlocal storage_scan_active
        if not storage_scan_active:
            return
        if (time.time() - storage_scan_last_activity) < 1.2:
            return
        storage_scan_active = False
        apply_scanned_paths()
        found_total = len(storage_scan_paths)
        set_scan_status(f"Dateien gefunden: {found_total}")
        notify("Dateiliste aktualisiert")
        page.update()

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

    def back_to_home(_: ft.ControlEvent) -> None:
        main_tabs.selected_index = 0
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

    def guarded_call(feature_key: str, callback, action_label: str = "Aktion") -> bool:
        if not is_enabled(feature_key):
            message = feature_hint(feature_key)
            append_log(f"[INFO] {message}")
            notify(message, error=True)
            return False
        if not serial_client.is_connected:
            append_log("[WARN] Kein Flipper verbunden")
            notify("Kein Flipper verbunden. Bitte in Settings verbinden.", error=True)
            return False
        try:
            callback()
            append_log(f"[OK] {action_label}")
            notify(action_label)
            return True
        except Exception as exc:
            append_log(f"[ERROR] {exc}")
            notify(f"Fehler bei {action_label}: {exc}", error=True)
            return False

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
            notify(f"{len(ports)} Port(s) gefunden")
        else:
            append_log("[WARN] Keine passenden Flipper-Ports gefunden")
            notify("Keine passenden Flipper-Ports gefunden", error=True)

    def refresh_file_lists(_: ft.ControlEvent | None = None) -> None:
        nonlocal storage_scan_active, storage_scan_current_dir, storage_scan_last_activity

        def start_scan() -> None:
            nonlocal storage_scan_active, storage_scan_current_dir, storage_scan_last_activity
            storage_scan_active = True
            storage_scan_current_dir = ""
            storage_scan_last_activity = time.time()
            storage_scan_paths.clear()
            ir_paths.clear()
            nfc_paths.clear()
            subghz_paths.clear()
            badusb_paths.clear()
            for directory in scan_dirs:
                api.storage_list(directory)

        success = guarded_call(FEATURE_STORAGE, start_scan, "Dateien werden geladen")
        if success:
            append_log("[INFO] Dateiliste wird vom Flipper aktualisiert")
            set_scan_status("Dateien werden geladen …")
        else:
            set_scan_status("Dateien nicht geladen", error=True)
        page.update()

    def connect_selected_port() -> None:
        selected_port = (port_dropdown.value or "").strip()
        if not selected_port:
            append_log("[WARN] Bitte zuerst einen Port auswählen")
            notify("Bitte zuerst einen Port auswählen", error=True)
            return
        try:
            serial_client.connect(selected_port)
            settings["last_port"] = selected_port
            config_store.save_settings(settings)
            append_log(f"[INFO] Verbindung hergestellt: {selected_port}")
            notify(f"Verbunden: {selected_port}")
        except Exception as exc:
            append_log(f"[ERROR] Verbindung fehlgeschlagen: {exc}")
            notify(f"Verbindung fehlgeschlagen: {exc}", error=True)
        update_connection_status()

    def disconnect() -> None:
        serial_client.disconnect()
        update_connection_status()
        set_scan_status("Dateien: nicht geladen")
        notify("Verbindung getrennt")

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
            append_log("[WARN] Makro enthält keine Schritte")
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

        success = guarded_call(FEATURE_MACROS, execute, f"Makro gestartet: {selected}")
        if success:
            append_log(f"[INFO] Makro gestartet: {selected} ({len(commands)} Schritte)")
        page.update()

    def run_macro_by_name(name: str) -> None:
        if name in macros:
            macro_select.value = name
            commands = macros.get(name, [])
            if not commands:
                append_log(f"[WARN] Makro ist leer: {name}")
                notify(f"Makro ist leer: {name}", error=True)
                return

            def execute() -> None:
                for command in commands:
                    api.raw(command)

            success = guarded_call(FEATURE_MACROS, execute, f"Makro gestartet: {name}")
            if success:
                append_log(f"[INFO] Makro gestartet: {name} ({len(commands)} Schritte)")
        else:
            append_log(f"[WARN] Makro nicht gefunden: {name}")
            notify(f"Makro nicht gefunden: {name}", error=True)

    def required_path(value: str, label: str) -> str | None:
        clean = (value or "").strip()
        if clean:
            return clean
        append_log(f"[WARN] {label} fehlt")
        notify(f"{label} fehlt", error=True)
        return None

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
            "Schnellaktionen",
            "Schnellaktionen direkt vom Dashboard.",
            [
                ft.Row(
                    wrap=True,
                    spacing=8,
                    run_spacing=8,
                    controls=[
                        ft.ElevatedButton(
                            "Geräteinfo",
                            on_click=lambda _: (guarded_call(FEATURE_SYSTEM, api.device_info, "Geräteinfo geladen"), page.update()),
                            height=control_height(),
                        ),
                        ft.OutlinedButton(
                            "Vibro Test",
                            on_click=lambda _: (
                                guarded_call(FEATURE_SYSTEM, lambda: api.vibro(True), "Vibro an"),
                                guarded_call(FEATURE_SYSTEM, lambda: api.vibro(False), "Vibro aus"),
                                page.update(),
                            ),
                            height=control_height(),
                        ),
                        ft.OutlinedButton(
                            "Dateien anzeigen",
                            on_click=lambda _: (guarded_call(FEATURE_STORAGE, lambda: api.storage_list("/"), "Dateien geladen"), page.update()),
                            height=control_height(),
                        ),
                        ft.OutlinedButton(
                            "Neu starten",
                            on_click=lambda _: (guarded_call(FEATURE_SYSTEM, api.reboot_normal, "Neustart ausgelöst"), page.update()),
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
                            "OK",
                            on_click=lambda _: (guarded_call(FEATURE_REMOTE, lambda: api.input_send("ok", "short"), "OK ausgelöst"), page.update()),
                            height=control_height(),
                        ),
                        ft.OutlinedButton(
                            "Back",
                            on_click=lambda _: (guarded_call(FEATURE_REMOTE, lambda: api.input_send("back", "short"), "Zurück ausgelöst"), page.update()),
                            height=control_height(),
                        ),
                        ft.OutlinedButton(
                            "Makro: Status",
                            on_click=lambda _: (run_macro_by_name("Status"), page.update()),
                            height=control_height(),
                        ),
                    ],
                )
            ],
        )

        log_card = panel_card("Aktivitäten", "Rückmeldungen für schnellen Überblick.", [mini_log_console])

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
            "System & Übersicht",
            feature_hint(FEATURE_SYSTEM),
            [
                ft.Row(
                    wrap=True,
                    spacing=8,
                    run_spacing=8,
                    controls=[
                        ft.ElevatedButton(
                            "Geräteinfo",
                            on_click=lambda _: (guarded_call(FEATURE_SYSTEM, api.device_info, "Geräteinfo geladen"), page.update()),
                            height=control_height(),
                        ),
                        system_path_input,
                        ft.OutlinedButton(
                            "Ordner anzeigen",
                            on_click=lambda _: (
                                guarded_call(
                                    FEATURE_STORAGE,
                                    lambda: api.storage_list(system_path_input.value or "/"),
                                    f"Ordner geladen: {system_path_input.value or '/'}",
                                ),
                                page.update(),
                            ),
                            height=control_height(),
                        ),
                    ],
                ),
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
            "Fernsteuerung",
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
                                guarded_call(FEATURE_REMOTE, lambda: api.input_send(key_name, "short"), f"Taste ausgelöst: {key_name}"),
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
                                guarded_call(FEATURE_REMOTE, lambda: api.input_long_with_fallback(key_name), f"Langes Drücken: {key_name}"),
                                page.update(),
                            ),
                            height=control_height(),
                        )
                        for label, key in long_buttons.items()
                    ],
                ),
            ],
        )

    def on_storage_mkdir(_: ft.ControlEvent) -> None:
        path = required_path(storage_mkdir_path.value, "Ordner-Pfad")
        if not path:
            page.update()
            return
        guarded_call(FEATURE_STORAGE, lambda: api.raw(f"storage mkdir {path}"), f"Ordner erstellt: {path}")
        page.update()

    def on_storage_remove(_: ft.ControlEvent) -> None:
        path = required_path(storage_remove_path.value, "Lösch-Pfad")
        if not path:
            page.update()
            return
        guarded_call(FEATURE_STORAGE, lambda: api.raw(f"storage remove {path}"), f"Element gelöscht: {path}")
        page.update()

    def on_storage_read(_: ft.ControlEvent) -> None:
        path = required_path(storage_read_path.value, "Anzeigen-Pfad")
        if not path:
            page.update()
            return
        guarded_call(FEATURE_STORAGE, lambda: api.raw(f"storage read {path}"), f"Dateiinhalt geladen: {path}")
        page.update()

    def on_ir_send(_: ft.ControlEvent) -> None:
        path = required_path(ir_file_path.value, "IR-Datei-Pfad")
        if not path:
            page.update()
            return
        guarded_call(FEATURE_INFRARED, lambda: api.raw(f"ir tx {path}"), f"Signal gesendet: {path}")
        page.update()

    def on_ir_open(_: ft.ControlEvent) -> None:
        path = required_path(ir_file_path.value, "IR-Datei-Pfad")
        if not path:
            page.update()
            return
        guarded_call(FEATURE_INFRARED, lambda: api.raw(f"storage read {path}"), "Dateiinhalt angezeigt")
        page.update()

    def on_nfc_emulate(_: ft.ControlEvent) -> None:
        path = required_path(nfc_file_path.value, "NFC-Datei-Pfad")
        if not path:
            page.update()
            return
        guarded_call(FEATURE_NFC_RFID, lambda: api.raw(f"nfc emu {path}"), f"Emulation gestartet: {path}")
        page.update()

    def on_subghz_tx(_: ft.ControlEvent) -> None:
        path = required_path(subghz_file_path.value, "Sub-GHz-Datei-Pfad")
        if not path:
            page.update()
            return
        guarded_call(FEATURE_SUBGHZ, lambda: api.raw(f"subghz tx_from_file {path}"), f"Senden gestartet: {path}")
        page.update()

    def on_subghz_open(_: ft.ControlEvent) -> None:
        path = required_path(subghz_file_path.value, "Sub-GHz-Datei-Pfad")
        if not path:
            page.update()
            return
        guarded_call(FEATURE_SUBGHZ, lambda: api.raw(f"storage read {path}"), "Dateiinhalt angezeigt")
        page.update()

    def on_badusb_run(_: ft.ControlEvent) -> None:
        if not badusb_confirm.value:
            append_log("[WARN] Bestätigung fehlt")
            notify("Bitte zuerst BadUSB-Bestätigung aktivieren", error=True)
            page.update()
            return
        path = required_path(badusb_script_path.value, "BadUSB-Script-Pfad")
        if not path:
            page.update()
            return
        guarded_call(FEATURE_BADUSB, lambda: api.raw(f"badusb run {path}"), f"Ablauf gestartet: {path}")
        page.update()

    def on_badusb_open(_: ft.ControlEvent) -> None:
        path = required_path(badusb_script_path.value, "BadUSB-Script-Pfad")
        if not path:
            page.update()
            return
        guarded_call(FEATURE_BADUSB, lambda: api.raw(f"storage read {path}"), "Ablaufinhalt angezeigt")
        page.update()

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
                        ft.ElevatedButton(
                            "Anzeigen",
                            on_click=lambda _: (
                                guarded_call(
                                    FEATURE_STORAGE,
                                    lambda: api.storage_list(storage_list_path_input.value or "/"),
                                    f"Ordner geladen: {storage_list_path_input.value or '/'}",
                                ),
                                page.update(),
                            ),
                            height=control_height(),
                        ),
                        storage_list_path_input,
                    ],
                ),
                ft.Row(
                    wrap=True,
                    spacing=8,
                    run_spacing=8,
                    controls=[
                        ft.OutlinedButton(
                            "Ordner erstellen",
                            on_click=on_storage_mkdir,
                            height=control_height(),
                        ),
                        storage_mkdir_path,
                    ],
                ),
                ft.Row(
                    wrap=True,
                    spacing=8,
                    run_spacing=8,
                    controls=[
                        ft.OutlinedButton(
                            "Löschen",
                            on_click=on_storage_remove,
                            height=control_height(),
                        ),
                        storage_remove_path,
                    ],
                ),
                ft.Row(
                    wrap=True,
                    spacing=8,
                    run_spacing=8,
                    controls=[
                        ft.OutlinedButton(
                            "Inhalt anzeigen",
                            on_click=on_storage_read,
                            height=control_height(),
                        ),
                        storage_read_path,
                    ],
                ),
            ],
        )

    def build_infrared_module() -> ft.Control:
        return panel_card(
            "Infrarot",
            feature_hint(FEATURE_INFRARED),
            [
                ft.Row(
                    wrap=True,
                    spacing=8,
                    run_spacing=8,
                    controls=[
                        ft.ElevatedButton(
                            "Signal senden",
                            on_click=on_ir_send,
                            height=control_height(),
                        ),
                        ft.OutlinedButton(
                            "Lernen starten",
                            on_click=lambda _: (guarded_call(FEATURE_INFRARED, lambda: api.raw("ir rx"), "Lernmodus gestartet"), page.update()),
                            height=control_height(),
                        ),
                        ft.OutlinedButton(
                            "Dateiinhalt anzeigen",
                            on_click=on_ir_open,
                            height=control_height(),
                        ),
                    ],
                ),
                ft.Row(wrap=True, spacing=8, run_spacing=8, controls=[ir_file_path]),
            ],
        )

    def build_nfc_module() -> ft.Control:
        return panel_card(
            "NFC/RFID",
            feature_hint(FEATURE_NFC_RFID),
            [
                ft.Row(
                    wrap=True,
                    spacing=8,
                    run_spacing=8,
                    controls=[
                        ft.ElevatedButton(
                            "Karte erkennen",
                            on_click=lambda _: (
                                guarded_call(FEATURE_NFC_RFID, lambda: api.raw("nfc detect"), "Erkennung gestartet"),
                                page.update(),
                            ),
                            height=control_height(),
                        ),
                        ft.OutlinedButton(
                            "Karte lesen",
                            on_click=lambda _: (guarded_call(FEATURE_NFC_RFID, lambda: api.raw("nfc read"), "Lesen gestartet"), page.update()),
                            height=control_height(),
                        ),
                        ft.OutlinedButton(
                            "Datei emulieren",
                            on_click=on_nfc_emulate,
                            height=control_height(),
                        ),
                    ],
                ),
                ft.Row(wrap=True, spacing=8, run_spacing=8, controls=[nfc_file_path]),
            ],
        )

    def build_subghz_module() -> ft.Control:
        return panel_card(
            "Funk",
            feature_hint(FEATURE_SUBGHZ),
            [
                ft.Row(
                    wrap=True,
                    spacing=8,
                    run_spacing=8,
                    controls=[
                        ft.ElevatedButton(
                            "Empfang starten",
                            on_click=lambda _: (
                                guarded_call(FEATURE_SUBGHZ, lambda: api.raw("subghz rx"), "Empfang läuft"),
                                page.update(),
                            ),
                            height=control_height(),
                        ),
                        ft.OutlinedButton(
                            "Gespeichertes Signal senden",
                            on_click=on_subghz_tx,
                            height=control_height(),
                        ),
                        ft.OutlinedButton(
                            "Dateiinhalt anzeigen",
                            on_click=on_subghz_open,
                            height=control_height(),
                        ),
                    ],
                ),
                ft.Row(wrap=True, spacing=8, run_spacing=8, controls=[subghz_file_path]),
                ft.Text("Nur auf legalen Frequenzen nutzen.", color=ft.Colors.RED_300),
            ],
        )

    def build_badusb_module() -> ft.Control:
        return panel_card(
            "BadUSB",
            feature_hint(FEATURE_BADUSB),
            [
                ft.Row(
                    wrap=True,
                    spacing=8,
                    run_spacing=8,
                    controls=[
                        ft.ElevatedButton(
                            "Ablauf starten",
                            on_click=on_badusb_run,
                            height=control_height(),
                        ),
                        ft.OutlinedButton(
                            "Stoppen",
                            on_click=lambda _: (guarded_call(FEATURE_BADUSB, lambda: api.raw("badusb stop"), "Ablauf gestoppt"), page.update()),
                            height=control_height(),
                        ),
                        ft.OutlinedButton(
                            "Ablaufinhalt anzeigen",
                            on_click=on_badusb_open,
                            height=control_height(),
                        ),
                    ],
                ),
                ft.Row(wrap=True, spacing=8, run_spacing=8, controls=[badusb_script_path]),
                badusb_confirm,
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
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Row(
                            spacing=8,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.OutlinedButton("Zurück", on_click=back_to_home, height=control_height()),
                                ft.Text(f"Modul: {selected_module}", size=23, weight=ft.FontWeight.BOLD),
                            ],
                        ),
                        ft.Row(
                            spacing=10,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                scan_status_text,
                                ft.OutlinedButton("Dateien aktualisieren", on_click=refresh_file_lists, height=control_height()),
                            ],
                        ),
                    ],
                ),
                module_tabs,
                module_panel_content,
            ],
        )

    def on_scan(_: ft.ControlEvent) -> None:
        perform_scan()
        page.update()

    def on_connect(_: ft.ControlEvent) -> None:
        connect_selected_port()
        if serial_client.is_connected:
            refresh_file_lists()
        page.update()

    def on_disconnect(_: ft.ControlEvent) -> None:
        disconnect()
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
            "Aktivitäten",
            "Status und Rückmeldungen vom Flipper.",
            [
                ft.Row(
                    spacing=8,
                    controls=[
                        ft.OutlinedButton(
                            "Verlauf leeren",
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
                    process_scan_line(line)
                page.update()
            finish_scan_if_idle()
            await asyncio.sleep(0.2)

    page.run_task(pump_logs)
