from setuptools import setup
from py2app.build_app import py2app as _py2app

APP = ["src/main.py"]
OPTIONS = {
    "argv_emulation": False,
    "packages": ["flet", "flet_desktop", "serial"],
    "plist": {
        "CFBundleName": "Flipper Zero Desktop Remote",
        "CFBundleDisplayName": "Flipper Zero Desktop Remote",
        "CFBundleIdentifier": "com.jokeks.flipperzerodesktopremote",
        "CFBundleShortVersionString": "0.1.0",
        "CFBundleVersion": "0.1.0",
        "LSMinimumSystemVersion": "13.0",
    },
}


class PatchedPy2App(_py2app):
    def finalize_options(self) -> None:
        if getattr(self.distribution, "install_requires", None):
            self.distribution.install_requires = []
        super().finalize_options()

setup(
    app=APP,
    options={"py2app": OPTIONS},
    cmdclass={"py2app": PatchedPy2App},
    setup_requires=["py2app"],
)
