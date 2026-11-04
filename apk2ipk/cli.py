import argparse
import json
from pathlib import Path
import shutil
import sys
import tarfile
import zipfile
from . import __version__
from .analyze import inspect_apk, markdown, write_report
from .archive import ConversionError
from .convert import convert
from .package import verify_ipk


def parser():
    p = argparse.ArgumentParser(description="APK → LG webOS: inspect, port web assets, package. Android runtime conversion is not supported.")
    p.add_argument("--version", action="version", version=__version__)
    commands = p.add_subparsers(dest="command", required=True)
    a = commands.add_parser("analyze", help="Inspect an APK without executing it")
    a.add_argument("apk")
    a.add_argument("--output", type=Path, help="New directory for JSON and Markdown reports")
    a.add_argument("--json", action="store_true")
    c = commands.add_parser("convert", help="Create a webOS project and IPK from reviewed web assets")
    c.add_argument("apk", nargs="?")
    c.add_argument("--web-dir", type=Path, help="Ported web export; takes precedence over APK assets")
    c.add_argument("--asset-root", help="APK member prefix, e.g. assets/www")
    c.add_argument("--entry", default="index.html")
    c.add_argument("--bootstrap-script", help="Generate entry HTML around this browser JS script, relative to the selected web folder")
    c.add_argument("--id", required=True, dest="app_id")
    c.add_argument("--title", required=True)
    c.add_argument("--app-version", default="1.0.0", dest="version")
    c.add_argument("--output", type=Path, required=True)
    c.add_argument("--project-only", action="store_true")
    c.add_argument("--acknowledge-limitations", action="store_true", dest="acknowledge", help="Optional acknowledgement recorded in the build report; never required")
    v = commands.add_parser("verify", help="Check IPK structure, metadata, entry point and icon")
    v.add_argument("ipk")
    commands.add_parser("gui", help="Open local desktop interface")
    commands.add_parser("doctor", help="Show runtime and optional tool availability")
    return p


def main(argv=None):
    p = parser()
    args = vars(p.parse_args(argv))
    command = args.pop("command")
    try:
        if command == "analyze":
            result = inspect_apk(args["apk"])
            if args["output"]:
                if args["output"].exists():
                    raise ConversionError("Report output must be a new directory.")
                write_report(result, args["output"])
            print(json.dumps(result, indent=2, ensure_ascii=False) if args["json"] else markdown(result))
        elif command == "convert":
            args["apk_path"] = args.pop("apk")
            print(json.dumps(convert(**args), indent=2, ensure_ascii=False))
        elif command == "verify":
            print(json.dumps(verify_ipk(args["ipk"]), indent=2, ensure_ascii=False))
        elif command == "doctor":
            print(json.dumps({"python": sys.version.split()[0], "apk2ipk": __version__,
                              "ares-package": shutil.which("ares-package"),
                              "note": "Core analysis and packaging need only Python. GUI additionally needs Tk. LG CLI is optional for official repackaging, installation and inspection."}, indent=2))
        elif command == "gui":
            from .gui import launch
            launch()
        return 0
    except (ConversionError, OSError, ValueError, KeyError, zipfile.BadZipFile, RuntimeError, tarfile.TarError, ImportError) as e:
        print(f"apk2ipk: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
