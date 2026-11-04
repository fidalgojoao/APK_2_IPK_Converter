"""Evidence-based feasibility reporting, never a compatibility guarantee."""
import hashlib
import json
from pathlib import Path
import re
from .archive import APK, ConversionError
from .manifest import parse_manifest, metadata
from .recover import discover_entries

RULES = [
    ("cordova", r"\bcordova\b|\bPhoneGap\b", "Cordova/PhoneGap bridge", "Port each plugin to browser or documented webOS APIs. Android cordova.js is not a webOS runtime."),
    ("capacitor", r"\bCapacitor\b", "Capacitor runtime", "Replace native plugins; build a web export and remove Android-only bootstrapping."),
    ("android-bridge", r"\bAndroid\s*\.|addJavascriptInterface|webkit\.messageHandlers|android_asset|capacitor://|https?://localhost", "Native bridge or Android asset URL", "Replace bridge calls and Android URL routing with webOS/browser implementations."),
    ("drm", r"Widevine|MediaDrm|com\.widevine|requestMediaKeySystemAccess", "DRM integration", "Confirm TV DRM support, licensing and provider authorization. Android DRM sessions cannot be copied."),
    ("billing", r"com\.android\.vending\.BILLING|BillingClient|com\.google\.android\.gms", "Google services / billing", "Implement supported sign-in, payments and service APIs for webOS; retain server authorization."),
    ("react-native", r"libreactnative|index\.android\.bundle|libhermes", "React Native / Hermes", "Port from source to a web-capable renderer; a JS bundle is not a standalone HTML app."),
    ("flutter", r"libflutter|flutter_assets", "Flutter Android engine", "Build Flutter web from original source and test its webOS browser requirements."),
    ("unity", r"libunity|libil2cpp", "Unity Android player", "Rebuild for a supported web target from the original Unity project; validate WebGL and memory on TV."),
    ("network", r"https?://", "Network endpoints", "Check CORS, TLS, authentication, redirects and service terms on the actual TV browser."),
]


def scan_web(files: dict[str, bytes]) -> list[dict]:
    found = {}
    for name, data in files.items():
        if name.startswith("_apk2ipk/") or data.startswith(b"\x03\x00\x08\x00"):
            continue
        if not name.lower().endswith((".js", ".mjs", ".html", ".htm", ".json", ".xml", ".css")):
            continue
        if len(data) > 4 * 1024 * 1024:
            found.setdefault("scan-limit", {"id": "scan-limit", "title": "Large text asset not scanned", "action": "Review text assets larger than 4 MiB manually.", "evidence": []})["evidence"].append(name)
            continue
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            continue
        for key, pattern, title, action in RULES:
            if re.search(pattern, text + "\n" + name, re.I):
                found.setdefault(key, {"id": key, "title": title, "action": action, "evidence": []})["evidence"].append(name)
    return list(found.values())


def inspect_apk(path: str | Path) -> dict:
    path = Path(path)
    with APK(path) as apk:
        manifest = metadata(parse_manifest(apk.read("AndroidManifest.xml", 8 * 1024 * 1024)))
        if manifest["split"]:
            raise ConversionError("This is a split APK. Supply the standalone/base APK and obtain a complete web export if assets are split.")
        names = sorted(apk.members)
        scripts = {n: apk.read(n, 4 * 1024 * 1024) for n in names
                   if n.startswith(("assets/", "res/raw/")) and n.lower().endswith((".js", ".mjs", ".html", ".htm", ".json", ".xml", ".css"))
                   and apk.members[n].file_size <= 4 * 1024 * 1024}
        candidates, components = discover_entries(scripts)
        findings = scan_web(scripts)
        for component in components:
            findings.append(dict(id="native-html-template", title="Embedded HTML component needs Android integration",
                                 action="This is a component, not a recovered app. " + "; ".join(component["dependencies"]), evidence=[component["path"]]))
        large = [n for n in names if n.startswith("assets/") and n.lower().endswith((".js", ".html", ".json", ".xml", ".css")) and apk.members[n].file_size > 4 * 1024 * 1024]
        if large:
            findings.append({"id": "scan-limit", "title": "Large text assets not scanned", "action": "Review these files manually.", "evidence": large})
        native = [n for n in names if n.endswith(".so")]
        dex = [n for n in names if re.fullmatch(r"classes\d*\.dex", n)]
        findings.append({"id": "android-runtime", "title": "Android runtime boundary", "action": "DEX, Android components, resources and native Android libraries are not translated. Only the selected web assets enter the IPK.", "evidence": dex + native + [c["name"] for c in manifest["components"]]})
        for key, pattern, title, action in RULES:
            evidence = [n for n in names + manifest["permissions"] if re.search(pattern, n, re.I)]
            if evidence and not any(f["id"] == key for f in findings):
                findings.append({"id": key, "title": title, "action": action, "evidence": evidence})
        if manifest["permissions"] or manifest["features"]:
            findings.append({"id": "permissions", "title": "Android permissions and hardware", "action": "Review each declaration. Android permissions do not grant webOS access; map only supported hardware and services.", "evidence": manifest["permissions"] + manifest["features"]})
        with path.open("rb") as source:
            digest = hashlib.file_digest(source, "sha256").hexdigest()
        result = {"schema_version": 1, "source_name": path.name,
                  "sha256": digest,
                  "manifest": manifest, "member_count": len(names),
                  "web_candidates": candidates, "embedded_web_components": components,
                  "dex_files": dex, "native_libraries": native,
                  "status": "web-assets-need-review" if candidates else "source-port-required",
                  "findings": findings,
                  "limits": ["Static inventory and text heuristics only; no complete call graph, DEX decompilation or behavior verification.",
                             "Android resource references (labels/icons) remain unresolved; supply webOS metadata explicitly.",
                             "An HTML entry is a candidate, not proof of a complete web app.",
                             "No Android code is run, no remote endpoints are contacted, and no secrets are sent to external services."]}
    return result


def markdown(report: dict) -> str:
    m = report["manifest"]
    lines = ["# APK compatibility report", "", f"Source: `{report['source_name']}`", f"SHA-256: `{report['sha256']}`",
             f"Android package: `{m['package']}`", f"Assessment: **{report['status']}**", "",
             "Packaging web assets is not Android runtime conversion. UI/API parity has not been verified.", "", "## Web candidates"]
    lines += [f"- `{c['path']}` ({c['kind']}; generated HTML: {c['generated']})" for c in report["web_candidates"]] or ["No standalone browser entry detected. Supply a ported web export."]
    if report.get("embedded_web_components"):
        lines += ["", "## Embedded HTML components (not complete apps)"]
        lines += [f"- `{c['path']}`: " + "; ".join(c["dependencies"]) for c in report["embedded_web_components"]]
    for f in report["findings"]:
        lines += ["", "## " + f["title"], f["action"]]
        lines += [f"- `{v}`" for v in f["evidence"][:80]]
        if len(f["evidence"]) > 80:
            lines += ["Additional evidence is included in report.json."]
    lines += ["", "## Scope and limitations"] + ["- " + x for x in report["limits"]]
    return "\n".join(lines) + "\n"


def write_report(report: dict, directory: Path):
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    (directory / "REPORT.md").write_text(markdown(report), encoding="utf-8")
