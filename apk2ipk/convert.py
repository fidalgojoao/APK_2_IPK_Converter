"""Auditable project generation; dependency findings are informational."""
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
from .analyze import inspect_apk, scan_web, write_report
from .archive import APK, ConversionError, read_web_directory, safe_name
from .package import icon_png, make_ipk, validate_metadata, verify_ipk


def convert(*, apk_path=None, web_dir=None, output, app_id, title, version="1.0.0",
            asset_root=None, entry="index.html", acknowledge=False, project_only=False):
    if not apk_path and not web_dir:
        raise ConversionError("Supply an APK or a ported --web-dir.")
    output = Path(output).absolute()
    if output.exists():
        raise ConversionError("Output must be a new directory; existing work is never overwritten.")
    report = inspect_apk(apk_path) if apk_path else None
    if web_dir:
        if asset_root:
            raise ConversionError("Choose either APK asset-root or an external web directory.")
        files = read_web_directory(Path(web_dir))
        origin = "user-supplied-web-export"
    else:
        candidates = report["web_candidates"]
        if not asset_root:
            if len(candidates) != 1:
                raise ConversionError("No unique web root. Select --asset-root from the report or supply a source-built --web-dir. Native Android applications require a source port.")
            asset_root = candidates[0]["root"]
            if entry == "index.html":
                entry = candidates[0]["entry"]
        asset_root = safe_name(asset_root.rstrip("/"))
        if not asset_root.startswith("assets/"):
            raise ConversionError("APK web root must be inside assets/.")
        prefix = asset_root + "/"
        with APK(apk_path) as apk:
            files = {n[len(prefix):]: apk.read(n) for n in apk.members if n.startswith(prefix)}
        origin = "apk-web-assets-only"
    safe_name(entry)
    if entry not in files:
        raise ConversionError(f"HTML entry not found in selected web root: {entry}")
    # Copy optional webOS metadata from an existing port; CLI choices are explicit overrides.
    info = json.loads(files.get("appinfo.json", b"{}"))
    if not isinstance(info, dict):
        raise ConversionError("Existing appinfo.json must be an object.")
    info.update(id=app_id, title=title, version=version, main=entry, type="web")
    info.setdefault("resolution", "1920x1080")
    info.setdefault("requiredACG", [])
    if not info.get("icon"):
        icon_name = "apk2ipk-icon.png"
        if icon_name in files:
            raise ConversionError("Generated icon name collides with a web asset; provide icon in appinfo.json.")
        files[icon_name] = icon_png()
        info["icon"] = icon_name
    if info["icon"] not in files or not files[info["icon"]].startswith(b"\x89PNG\r\n\x1a\n"):
        raise ConversionError("The webOS icon must reference an existing PNG.")
    validate_metadata(info)
    findings = scan_web(files)
    conversion = {"schema_version": 1, "mode": origin, "appinfo": info,
                  "android_code_translated": False, "runtime_verified": False,
                  "acknowledged_limitations": acknowledge, "web_findings": findings,
                  "findings_policy": "informational-only; no features filtered or bridge calls rewritten",
                  "source_apk_sha256": report["sha256"] if report else None,
                  "asset_sha256": {n: hashlib.sha256(d).hexdigest() for n, d in sorted(files.items())},
                  "excluded_android_content": ["DEX code", "Android native libraries", "Android manifest and resources", "Android permissions and services"],
                  "validation_required": ["Launch and navigation using LG remote", "Authentication and external APIs", "Media codecs and DRM", "All native bridge/plugin replacements", "Target webOS browser compatibility, storage and lifecycle"]}
    files["appinfo.json"] = json.dumps(info, indent=2, ensure_ascii=False).encode()
    output.parent.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix=".apk2ipk-", dir=output.parent))
    try:
        app = temp / "app"
        app.mkdir()
        for name, data in files.items():
            dest = app / safe_name(name)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
        if report:
            write_report(report, temp / "analysis")
        (temp / "conversion.json").write_text(json.dumps(conversion, indent=2, ensure_ascii=False), encoding="utf-8")
        (temp / "TESTING.md").write_text("# TV acceptance checklist\n\nThis package has not been verified on a TV.\n\n" + "\n".join("- [ ] " + s for s in conversion["validation_required"]) + "\n", encoding="utf-8")
        if not project_only:
            name = f"{app_id}_{version}_all.ipk"
            (temp / name).write_bytes(make_ipk(files, info))
            verified = verify_ipk(temp / name)
            (temp / "verification.json").write_text(json.dumps(verified, indent=2), encoding="utf-8")
        temp.rename(output)
    except BaseException:
        shutil.rmtree(temp)
        raise
    return {"output": str(output), "ipk": str(output / name) if not project_only else None,
            "web_findings": findings, "runtime_verified": False}
