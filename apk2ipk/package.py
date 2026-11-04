"""Deterministic webOS IPK writer and bounded structural verifier."""
import gzip
import io
import json
from pathlib import Path
import re
import struct
import tarfile
import zlib
from .archive import ConversionError, safe_name, MAX_TOTAL, MAX_FILE, MAX_FILES


def validate_metadata(info: dict):
    if not isinstance(info, dict):
        raise ConversionError("appinfo.json must be a JSON object.")
    for key in ("id", "title", "version", "main", "icon", "type"):
        if not isinstance(info.get(key), str) or not info[key] or any(ord(c) < 32 for c in info[key]):
            raise ConversionError(f"Invalid/missing appinfo field: {key}")
    if not re.fullmatch(r"[a-z0-9][a-z0-9.-]{1,127}", info["id"]) or info["id"].startswith(("com.palm", "com.webos", "com.lge", "com.palmdts")):
        raise ConversionError("Invalid or reserved webOS application ID.")
    if not re.fullmatch(r"(0|[1-9]\d{0,8})\.(0|[1-9]\d{0,8})\.(0|[1-9]\d{0,8})", info["version"]):
        raise ConversionError("Version must be three integers without leading zeros (for example 1.0.0).")
    if info["type"] != "web":
        raise ConversionError("Only LG webOS web apps are supported.")
    if "requiredACG" in info and (not isinstance(info["requiredACG"], list) or any(not isinstance(x, str) or not x for x in info["requiredACG"])):
        raise ConversionError("requiredACG must be an array of group names.")
    safe_name(info["main"])
    safe_name(info["icon"])
    if not info["main"].lower().endswith((".html", ".htm")):
        raise ConversionError("Entry point must be a local HTML file.")


def icon_png(size=80) -> bytes:
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))
    raw = b"".join(b"\0" + bytes((28, 190, 160, 255)) * size for _ in range(size))
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")


def tar_gz(files: dict[str, bytes]) -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w", format=tarfile.USTAR_FORMAT) as tar:
        dirs = set()
        for name in files:
            p = Path(name).parent
            while str(p) != ".":
                dirs.add(p.as_posix())
                p = p.parent
        for name in sorted(dirs):
            entry = tarfile.TarInfo("./" + name)
            entry.type, entry.mode = tarfile.DIRTYPE, 0o755
            tar.addfile(entry)
        for name, data in sorted(files.items()):
            entry = tarfile.TarInfo("./" + name)
            entry.mode, entry.size = 0o644, len(data)
            tar.addfile(entry, io.BytesIO(data))
    return gzip.compress(buf.getvalue(), mtime=0)


def make_ipk(files: dict[str, bytes], info: dict) -> bytes:
    validate_metadata(info)
    base = "usr/palm/applications/" + info["id"] + "/"
    data = {base + safe_name(n): d for n, d in files.items()}
    data[base + "appinfo.json"] = json.dumps(info, indent=2, ensure_ascii=False).encode()
    package_info = {"id": info["id"], "version": info["version"], "app": info["id"], "loc_name": info["title"], "vendor": info.get("vendor", "APK2IPK")}
    data["usr/palm/packages/" + info["id"] + "/packageinfo.json"] = json.dumps(package_info, ensure_ascii=False).encode()
    control = (f"Package: {info['id']}\nVersion: {info['version']}\nSection: misc\nPriority: optional\nArchitecture: all\nMaintainer: APK2IPK\nDescription: LG webOS web application\n").encode()
    members = {"debian-binary": b"2.0\n", "control.tar.gz": tar_gz({"control": control}), "data.tar.gz": tar_gz(data)}
    result = bytearray(b"!<arch>\n")
    for name, payload in members.items():
        header = f"{name + '/':<16}{0:<12}{0:<6}{0:<6}{'100644':<8}{len(payload):<10}`\n".encode("ascii")
        result += header + payload + (b"\n" if len(payload) % 2 else b"")
    return bytes(result)


def _tar_files(payload: bytes) -> dict[str, bytes]:
    out = {}
    seen = set()
    total = 0
    with tarfile.open(fileobj=io.BytesIO(payload), mode="r:gz") as tar:
        count = 0
        for member in tar:
            count += 1
            if count > MAX_FILES * 3:
                raise ConversionError("Too many tar entries.")
            name = member.name[2:] if member.name.startswith("./") else member.name
            if name in ("", ".") and member.isdir():
                continue
            safe_name(name.rstrip("/"))
            if member.isdir():
                continue
            if not member.isfile() or member.size > MAX_FILE or member.size < 0:
                raise ConversionError("Unsupported/oversized tar member.")
            if name.casefold() in seen:
                raise ConversionError("Duplicate tar entry.")
            seen.add(name.casefold())
            total += member.size
            if total > MAX_TOTAL:
                raise ConversionError("Expanded IPK exceeds 512 MiB.")
            stream = tar.extractfile(member)
            out[name] = stream.read(MAX_FILE + 1)
    return out


def verify_ipk(path: str | Path) -> dict:
    path = Path(path)
    if path.stat().st_size > MAX_TOTAL:
        raise ConversionError("IPK exceeds 512 MiB.")
    data = path.read_bytes()
    if not data.startswith(b"!<arch>\n"):
        raise ConversionError("Not an ar-format IPK.")
    pos, members = 8, {}
    while pos < len(data):
        header = data[pos:pos + 60]
        if len(header) != 60 or header[58:] != b"`\n":
            raise ConversionError("Invalid ar header.")
        name = header[:16].decode("ascii").strip().rstrip("/")
        size = int(header[48:58])
        pos += 60
        if size < 0 or pos + size > len(data) or name in members:
            raise ConversionError("Invalid ar extent or duplicate member.")
        members[name] = data[pos:pos + size]
        pos += size
        if size % 2:
            if data[pos:pos + 1] != b"\n":
                raise ConversionError("Invalid ar padding.")
            pos += 1
    if set(members) != {"debian-binary", "control.tar.gz", "data.tar.gz"} or members["debian-binary"] != b"2.0\n":
        raise ConversionError("IPK is missing required Debian members.")
    controls = _tar_files(members["control.tar.gz"])
    files = _tar_files(members["data.tar.gz"])
    apps = [n for n in files if re.fullmatch(r"usr/palm/applications/[^/]+/appinfo.json", n)]
    if len(apps) != 1 or "control" not in controls:
        raise ConversionError("Expected exactly one webOS application and control file.")
    info = json.loads(files[apps[0]])
    validate_metadata(info)
    base = "usr/palm/applications/" + info["id"] + "/"
    if apps[0] != base + "appinfo.json" or base + info["main"] not in files or base + info["icon"] not in files:
        raise ConversionError("Application root, entry or icon is missing/mismatched.")
    control = dict(line.split(": ", 1) for line in controls["control"].decode().splitlines() if ": " in line)
    if control.get("Package") != info["id"] or control.get("Version") != info["version"] or control.get("Architecture") != "all":
        raise ConversionError("Control metadata does not match appinfo.json.")
    return {"valid_structure": True, "appinfo": info, "file_count": len(files),
            "runtime_verified": False, "note": "Structural verification only. Install and test on your target LG TV."}
