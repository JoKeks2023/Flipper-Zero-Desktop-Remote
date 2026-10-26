# Third-party software and credits

Flipper Remote's own source is MIT licensed (see LICENSE). This does not
relicense third-party components. Retain their notices when redistributing them.

## Runtime components

- Qt, PySide6-Essentials and Shiboken6 — The Qt Company and contributors.
  Qt for Python is available under LGPLv3/GPLv3 or commercial licensing.
  The applicable terms depend on the distributed components and chosen license.
  https://doc.qt.io/qtforpython-6/licenses.html
  https://code.qt.io/cgit/pyside/pyside-setup.git/
- pySerial — Chris Liechti and contributors, BSD-3-Clause.
  https://github.com/pyserial/pyserial/blob/master/LICENSE.txt
- Optional Model Context Protocol Python SDK and mcp-types — MCP contributors,
  MIT. https://github.com/modelcontextprotocol/python-sdk/blob/main/LICENSE
- Python — Python Software Foundation and contributors, PSF License Agreement
  and incorporated notices. https://docs.python.org/3/license.html

Release packages include a `licenses/` directory with installed distribution notices,
upstream Qt license/attribution files and a versioned build-environment manifest.
This manifest is a superset, including build tools. See
[Binary components and matching sources](docs/binary-components.md) for locations,
source links and instructions for replacing the dynamically loaded Qt libraries.
This source overview is not itself the complete notice inventory.

## Device ecosystem

- Flipper Devices — Flipper Zero hardware and the public CLI/protobuf protocol.
  https://github.com/flipperdevices/flipperzero-protobuf
- Momentum community — Momentum Firmware.
  https://github.com/Next-Flip/Momentum-Firmware
- Project contributors and community — issue reports, ideas and patches.
  https://github.com/JoKeks2023/Flipper-Zero-Desktop-Remote/graphs/contributors

Firmware and hardware are not distributed as part of this desktop application.
Project and product names belong to their respective owners. These credits do
not imply endorsement or an official relationship with those projects.
