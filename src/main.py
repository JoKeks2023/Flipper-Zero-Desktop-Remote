"""Desktop entry point; the same standalone executable also serves MCP over stdio."""
import sys

VERSION = "0.2.0"


def main() -> None:
    if "--version" in sys.argv[1:]:
        print(VERSION)
        return
    if sys.argv[1:2] == ["--mcp"]:
        del sys.argv[1]
        from flipper_mcp.server import main as serve
        serve()
        return
    if sys.argv[1:] == ["--smoke-test"]:
        from ui.smoke import run as smoke
        smoke()
        return
    from ui.app import run
    run()


if __name__ == "__main__":
    main()
