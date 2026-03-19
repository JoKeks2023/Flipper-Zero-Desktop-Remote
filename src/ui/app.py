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
    page.theme_mode = ft.ThemeMode.DARK
    page.scroll = ft.ScrollMode.AUTO
    page.padding = 20
    page.window_width = 1200
    page.window_height = 840

    serial_client = SerialClient()
    api = FlipperAPI(serial_client.send_command)
    config_store = ConfigStore(app_name)
    settings = config_store.load_settings()
    macros = config_store.load_macros()
    capabilities = build_capabilities(bool(settings.get("expert_mode", False)))

    log_lines: list[str] = []
    max_log_lines = 2000

    header = ft.Text(app_name, size=28, weight=ft.FontWeight.BOLD)
    subtitle = ft.Text(
        "Desktop-Steuerung für Flipper-Funktionen ohne Navigation im Gerät-Menü.",
        color=ft.Colors.ORANGE_200,
    )

    status_chip = ft.Container(
        content=ft.Text("Nicht verbunden", color=ft.Colors.WHITE),
        bgcolor=ft.Colors.RED_700,
        padding=8,
        border_radius=8,
    )

    port_dropdown = ft.Dropdown(label="Flipper Port", width=420, options=[])
    raw_cmd_input = ft.TextField(label="Raw CLI", hint_text="Befehl eingeben", expand=True)

    log_console = ft.TextField(
        label="Log-Konsole",
        multiline=True,
        min_lines=13,
        max_lines=13,
        read_only=True,
        value="",
    )

    system_path_input = ft.TextField(label="Storage Pfad", value="/", width=300)
    storage_list_path_input = ft.TextField(label="Listen-Pfad", value="/", width=320)
    storage_upload_local = ft.TextField(label="Lokale Datei (Pfad)", value="", width=360)
    storage_upload_remote = ft.TextField(label="Ziel auf Flipper", value="/ext/", width=300)
    storage_download_remote = ft.TextField(label="Quelle auf Flipper", value="/ext/", width=300)
    storage_download_local = ft.TextField(label="Lokaler Zielpfad", value="", width=360)

    ir_command_input = ft.TextField(label="IR CLI", value="ir tx /ext/infrared/example.ir", expand=True)
    nfc_command_input = ft.TextField(label="NFC/RFID CLI", value="nfc detect", expand=True)
    subghz_command_input = ft.TextField(label="Sub-GHz CLI", value="subghz rx", expand=True)
    badusb_command_input = ft.TextField(label="BadUSB CLI", value="badusb run /ext/badusb/script.txt", expand=True)
    badusb_confirm = ft.Checkbox(label="Ich bestätige kontrollierte/legitime Nutzung", value=False)

    macro_select = ft.Dropdown(label="Gespeichertes Makro", width=300, options=[])
    macro_name_input = ft.TextField(label="Makro-Name", width=260)
    macro_commands_input = ft.TextField(
        label="Makro-Befehle (eine Zeile = ein Befehl)",
        multiline=True,
        min_lines=6,
        max_lines=8,
    )

    expert_mode_checkbox = ft.Checkbox(
        label="Expert-Mode (NFC/Sub-GHz/BadUSB freischalten)",
        value=bool(settings.get("expert_mode", False)),
    )

    module_order = [
        "System",
        "Remote",
        "Storage",
        "Infrared",
        "NFC/RFID",
        "Sub-GHz",
        "BadUSB",
        "Makros",
        "Settings",
    ]
    module_tabs = ft.Tabs(
        content=ft.Row([ft.Tab(label=name) for name in module_order]),
        length=len(module_order),
        selected_index=0,
        animation_duration=150,
        expand=1,
    )
    module_content = ft.Container(expand=True)

    def append_log(line: str) -> None:
        log_lines.append(line)
        if len(log_lines) > max_log_lines:
            del log_lines[: len(log_lines) - max_log_lines]
        log_console.value = "\n".join(log_lines)

    def update_connection_status() -> None:
        if serial_client.is_connected:
            status_chip.content = ft.Text("Verbunden", color=ft.Colors.WHITE)
            status_chip.bgcolor = ft.Colors.GREEN_700
        else:
            status_chip.content = ft.Text("Nicht verbunden", color=ft.Colors.WHITE)
            status_chip.bgcolor = ft.Colors.RED_700

    def is_enabled(feature_key: str) -> bool:
        capability = capabilities.get(feature_key)
        return bool(capability and capability.enabled)

    def feature_hint(feature_key: str) -> str:
        capability = capabilities.get(feature_key)
        if not capability:
            return "Feature-Zustand unbekannt"
        return capability.hint

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
        if not selected_name or selected_name not in macros:
            return
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

    def disabled_panel(title: str, message: str) -> ft.Control:
        return ft.Container(
            padding=16,
            border_radius=10,
            bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.ORANGE_400),
            content=ft.Column(
                spacing=8,
                controls=[
                    ft.Text(title, size=16, weight=ft.FontWeight.BOLD),
                    ft.Text(message),
                ],
            ),
        )

    def build_system_tab() -> ft.Control:
        return ft.Column(
            spacing=10,
            controls=[
                ft.Text("System & Diagnose", size=18, weight=ft.FontWeight.W_600),
                ft.Text(feature_hint(FEATURE_SYSTEM), color=ft.Colors.GREY_400),
                ft.Row(
                    wrap=True,
                    spacing=8,
                    run_spacing=8,
                    controls=[
                        ft.ElevatedButton(
                            "Device Info",
                            on_click=lambda _: (guarded_call(FEATURE_SYSTEM, api.device_info), page.update()),
                        ),
                        ft.OutlinedButton(
                            "Storage Root",
                            on_click=lambda _: (
                                guarded_call(FEATURE_STORAGE, lambda: api.storage_list(system_path_input.value or "/")),
                                page.update(),
                            ),
                        ),
                        ft.OutlinedButton(
                            "Vibro Test",
                            on_click=lambda _: (
                                guarded_call(FEATURE_SYSTEM, lambda: api.vibro(True)),
                                guarded_call(FEATURE_SYSTEM, lambda: api.vibro(False)),
                                page.update(),
                            ),
                        ),
                    ],
                ),
                system_path_input,
                ft.Text("Nutze Raw CLI unten für zusätzliche Momentum-Kommandos.", color=ft.Colors.GREY_500),
            ],
        )

    def build_remote_tab() -> ft.Control:
        if not is_enabled(FEATURE_REMOTE):
            return disabled_panel("Remote deaktiviert", feature_hint(FEATURE_REMOTE))

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

        return ft.Column(
            spacing=10,
            controls=[
                ft.Text("Remote Control", size=18, weight=ft.FontWeight.W_600),
                ft.Text(feature_hint(FEATURE_REMOTE), color=ft.Colors.GREY_400),
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
                        )
                        for label, key in long_buttons.items()
                    ],
                ),
                ft.Row(
                    wrap=True,
                    spacing=8,
                    run_spacing=8,
                    controls=[
                        ft.OutlinedButton(
                            "Reboot",
                            on_click=lambda _: (guarded_call(FEATURE_SYSTEM, api.reboot_normal), page.update()),
                        ),
                        ft.OutlinedButton(
                            "Bootloader",
                            on_click=lambda _: (guarded_call(FEATURE_SYSTEM, api.reboot_bootloader), page.update()),
                        ),
                        ft.OutlinedButton(
                            "Firmware Update",
                            on_click=lambda _: (
                                guarded_call(FEATURE_SYSTEM, api.reboot_firmware_update),
                                page.update(),
                            ),
                        ),
                    ],
                ),
            ],
        )

    def build_storage_tab() -> ft.Control:
        if not is_enabled(FEATURE_STORAGE):
            return disabled_panel("Storage deaktiviert", feature_hint(FEATURE_STORAGE))

        return ft.Column(
            spacing=10,
            controls=[
                ft.Text("Storage", size=18, weight=ft.FontWeight.W_600),
                ft.Text("Dateien verwalten über Momentum-CLI (Command-basiert).", color=ft.Colors.GREY_400),
                ft.Row(
                    wrap=True,
                    spacing=8,
                    controls=[
                        storage_list_path_input,
                        ft.ElevatedButton(
                            "List",
                            on_click=lambda event: (
                                guarded_call(
                                    FEATURE_STORAGE,
                                    lambda: api.storage_list(storage_list_path_input.value or "/"),
                                ),
                                page.update(),
                            ),
                        ),
                    ],
                ),
                ft.Row(
                    wrap=True,
                    spacing=8,
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
                        ),
                    ],
                ),
                ft.Row(
                    wrap=True,
                    spacing=8,
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
                        ),
                    ],
                ),
                ft.Text(
                    "Hinweis: Upload/Download-Templates hängen von CLI-Syntax deiner Firmware ab.",
                    color=ft.Colors.GREY_500,
                ),
            ],
        )

    def build_infrared_tab() -> ft.Control:
        if not is_enabled(FEATURE_INFRARED):
            return disabled_panel("Infrared deaktiviert", feature_hint(FEATURE_INFRARED))
        return ft.Column(
            spacing=10,
            controls=[
                ft.Text("Infrared", size=18, weight=ft.FontWeight.W_600),
                ft.Text("Sende oder teste IR-Kommandos über CLI.", color=ft.Colors.GREY_400),
                ir_command_input,
                ft.Row(
                    wrap=True,
                    spacing=8,
                    run_spacing=8,
                    controls=[
                        ft.ElevatedButton(
                            "IR ausführen",
                            on_click=lambda _: (guarded_call(FEATURE_INFRARED, lambda: api.raw(ir_command_input.value)), page.update()),
                        ),
                        ft.OutlinedButton(
                            "Template: Send File",
                            on_click=lambda _: (
                                setattr(ir_command_input, "value", "ir tx /ext/infrared/example.ir"),
                                page.update(),
                            ),
                        ),
                        ft.OutlinedButton(
                            "Template: Learn",
                            on_click=lambda _: (
                                setattr(ir_command_input, "value", "ir rx"),
                                page.update(),
                            ),
                        ),
                    ],
                ),
            ],
        )

    def build_nfc_tab() -> ft.Control:
        if not is_enabled(FEATURE_NFC_RFID):
            return disabled_panel("NFC/RFID deaktiviert", feature_hint(FEATURE_NFC_RFID))
        return ft.Column(
            spacing=10,
            controls=[
                ft.Text("NFC/RFID", size=18, weight=ft.FontWeight.W_600),
                ft.Text(feature_hint(FEATURE_NFC_RFID), color=ft.Colors.GREY_400),
                nfc_command_input,
                ft.Row(
                    wrap=True,
                    spacing=8,
                    run_spacing=8,
                    controls=[
                        ft.ElevatedButton(
                            "Ausführen",
                            on_click=lambda _: (guarded_call(FEATURE_NFC_RFID, lambda: api.raw(nfc_command_input.value)), page.update()),
                        ),
                        ft.OutlinedButton(
                            "Detect",
                            on_click=lambda _: (setattr(nfc_command_input, "value", "nfc detect"), page.update()),
                        ),
                        ft.OutlinedButton(
                            "Read",
                            on_click=lambda _: (setattr(nfc_command_input, "value", "nfc read"), page.update()),
                        ),
                    ],
                ),
            ],
        )

    def build_subghz_tab() -> ft.Control:
        if not is_enabled(FEATURE_SUBGHZ):
            return disabled_panel("Sub-GHz deaktiviert", feature_hint(FEATURE_SUBGHZ))
        return ft.Column(
            spacing=10,
            controls=[
                ft.Text("Sub-GHz", size=18, weight=ft.FontWeight.W_600),
                ft.Text(feature_hint(FEATURE_SUBGHZ), color=ft.Colors.GREY_400),
                subghz_command_input,
                ft.Row(
                    wrap=True,
                    spacing=8,
                    run_spacing=8,
                    controls=[
                        ft.ElevatedButton(
                            "Ausführen",
                            on_click=lambda _: (guarded_call(FEATURE_SUBGHZ, lambda: api.raw(subghz_command_input.value)), page.update()),
                        ),
                        ft.OutlinedButton(
                            "RX",
                            on_click=lambda _: (setattr(subghz_command_input, "value", "subghz rx"), page.update()),
                        ),
                        ft.OutlinedButton(
                            "TX",
                            on_click=lambda _: (setattr(subghz_command_input, "value", "subghz tx"), page.update()),
                        ),
                    ],
                ),
                ft.Text("Nur auf legalen Frequenzen nutzen.", color=ft.Colors.RED_300),
            ],
        )

    def build_badusb_tab() -> ft.Control:
        if not is_enabled(FEATURE_BADUSB):
            return disabled_panel("BadUSB deaktiviert", feature_hint(FEATURE_BADUSB))
        return ft.Column(
            spacing=10,
            controls=[
                ft.Text("BadUSB", size=18, weight=ft.FontWeight.W_600),
                ft.Text(feature_hint(FEATURE_BADUSB), color=ft.Colors.GREY_400),
                badusb_command_input,
                badusb_confirm,
                ft.ElevatedButton(
                    "BadUSB Befehl ausführen",
                    on_click=lambda _: (
                        append_log("[WARN] Bestätigung fehlt")
                        if not badusb_confirm.value
                        else guarded_call(FEATURE_BADUSB, lambda: api.raw(badusb_command_input.value)),
                        page.update(),
                    ),
                ),
            ],
        )

    def build_macros_tab() -> ft.Control:
        if not is_enabled(FEATURE_MACROS):
            return disabled_panel("Makros deaktiviert", feature_hint(FEATURE_MACROS))
        return ft.Column(
            spacing=10,
            controls=[
                ft.Text("Makros", size=18, weight=ft.FontWeight.W_600),
                ft.Text("Speichere und starte eigene Befehlssequenzen.", color=ft.Colors.GREY_400),
                ft.Row(wrap=True, spacing=8, controls=[macro_select, ft.OutlinedButton("Laden", on_click=load_selected_macro)]),
                ft.Row(wrap=True, spacing=8, controls=[macro_name_input]),
                macro_commands_input,
                ft.Row(
                    wrap=True,
                    spacing=8,
                    run_spacing=8,
                    controls=[
                        ft.ElevatedButton("Speichern", on_click=save_macro),
                        ft.OutlinedButton("Löschen", on_click=delete_macro),
                        ft.OutlinedButton("Ausführen", on_click=run_macro),
                    ],
                ),
            ],
        )

    def build_settings_tab() -> ft.Control:
        return ft.Column(
            spacing=12,
            controls=[
                ft.Text("Settings", size=18, weight=ft.FontWeight.W_600),
                ft.Text("Verbindung, Sicherheitsmodus und Debug-Konsole.", color=ft.Colors.GREY_400),
                top_controls,
                settings_row,
                raw_command_row,
                log_console,
            ],
        )

    def rebuild_module_panel() -> None:
        idx = module_tabs.selected_index if module_tabs.selected_index is not None else 0
        selected = module_order[idx]
        if selected == "System":
            module_content.content = build_system_tab()
        elif selected == "Remote":
            module_content.content = build_remote_tab()
        elif selected == "Storage":
            module_content.content = build_storage_tab()
        elif selected == "Infrared":
            module_content.content = build_infrared_tab()
        elif selected == "NFC/RFID":
            module_content.content = build_nfc_tab()
        elif selected == "Sub-GHz":
            module_content.content = build_subghz_tab()
        elif selected == "BadUSB":
            module_content.content = build_badusb_tab()
        elif selected == "Makros":
            module_content.content = build_macros_tab()
        elif selected == "Settings":
            module_content.content = build_settings_tab()
        else:
            module_content.content = build_system_tab()

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
        page.update()

    def on_module_change(_: ft.ControlEvent) -> None:
        rebuild_module_panel()
        page.update()

    expert_mode_checkbox.on_change = on_expert_mode_change
    module_tabs.on_change = on_module_change

    raw_command_row = ft.Row(
        spacing=8,
        controls=[
            raw_cmd_input,
            ft.ElevatedButton("Raw senden", on_click=on_send_raw),
            ft.OutlinedButton("Logs leeren", on_click=lambda _: (log_lines.clear(), setattr(log_console, "value", ""), page.update())),
        ],
    )

    top_controls = ft.Row(
        wrap=True,
        spacing=8,
        controls=[
            port_dropdown,
            ft.ElevatedButton("Scan", on_click=on_scan),
            ft.ElevatedButton("Connect", on_click=on_connect),
            ft.OutlinedButton("Disconnect", on_click=on_disconnect),
            status_chip,
        ],
    )

    settings_row = ft.Row(wrap=True, spacing=12, controls=[expert_mode_checkbox])

    page.add(
        ft.Column(
            spacing=12,
            controls=[
                header,
                subtitle,
                ft.Divider(height=1, color=ft.Colors.ORANGE_300),
                module_tabs,
                module_content,
            ],
        )
    )

    refresh_macro_dropdown()
    if macros:
        first_macro = sorted(macros.keys())[0]
        macro_select.value = first_macro
        macro_name_input.value = first_macro
        macro_commands_input.value = "\n".join(macros[first_macro])

    rebuild_module_panel()
    perform_scan()
    update_connection_status()
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
            await asyncio.sleep(0.15)

    page.run_task(pump_logs)
