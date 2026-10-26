"""Exercise the real packaged GUI process and the packaged stdio MCP server."""
import asyncio
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from mcp.client import Client
from mcp.client.stdio import StdioServerParameters

executable = str(Path(sys.argv[1]).resolve())
version = subprocess.check_output([executable, '--version'], text=True).strip()
assert version == '0.2.0', version

async def check_mcp():
    with tempfile.TemporaryDirectory() as directory:
        # No desktop app owns this deliberately absent socket. An actionable tool
        # error proves the frozen SDK, tool registration and local client ran.
        params = StdioServerParameters(command=executable, args=['--mcp', '--socket', directory + '/absent.sock'])
        async with Client(params, mode='legacy') as client:
            tools = (await client.list_tools()).tools
            assert len(tools) == 6, tools
            result = await client.call_tool('flipper_status', {})
            assert result.is_error, result
            assert 'App' in str(result.content) or 'app' in str(result.content), result
    print('Packaged MCP: handshake, six tools, desktop-unavailable error OK')

asyncio.run(check_mcp())
# The GUI smoke path instantiates all real pages, loads both themes and legal
# resources, checks minimum-size layout, then exits without touching user settings.
subprocess.run([executable, '--smoke-test'], env={**os.environ, 'QT_QPA_PLATFORM': 'offscreen'}, check=True, timeout=30)
