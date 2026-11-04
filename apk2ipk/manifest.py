"""Android binary XML decoder for manifest metadata; no code is executed."""
import struct
import xml.etree.ElementTree as ET
from .archive import ConversionError

ANDROID = "http://schemas.android.com/apk/res/android"


def parse_manifest(data: bytes) -> ET.Element:
    if len(data) > 8 * 1024 * 1024:
        raise ConversionError("Manifest exceeds 8 MiB.")
    if data.lstrip().startswith(b"<"):
        if b"<!DOCTYPE" in data.upper() or b"<!ENTITY" in data.upper():
            raise ConversionError("XML entities and DTDs are not supported.")
        try:
            root = ET.fromstring(data)
            if root.tag != "manifest":
                raise ConversionError("XML root must be manifest.")
            return root
        except ET.ParseError as e:
            raise ConversionError(f"Invalid manifest XML: {e}") from e
    try:
        return _binary(data)
    except (IndexError, struct.error, UnicodeError, ValueError) as e:
        raise ConversionError(f"Invalid Android binary manifest: {e}") from e


def _binary(data: bytes) -> ET.Element:
    u16 = lambda p: struct.unpack_from("<H", data, p)[0]
    u32 = lambda p: struct.unpack_from("<I", data, p)[0]
    if u16(0) != 3 or u16(2) != 8 or u32(4) != len(data):
        raise ValueError("not a complete binary XML document")
    strings = []
    stack = []
    root = None
    pos = 8
    while pos < len(data):
        kind, header, size = struct.unpack_from("<HHI", data, pos)
        end = pos + size
        if header < 8 or size < header or end > len(data):
            raise ValueError("invalid chunk extent")
        if kind == 1:
            if header < 28:
                raise ValueError("invalid string pool header")
            count, _, flags, start, _ = struct.unpack_from("<IIIII", data, pos + 8)
            if count > 100000 or header + count * 4 > size:
                raise ValueError("invalid string count")
            strings = []
            for i in range(count):
                cursor = pos + start + u32(pos + header + i * 4)
                def length(at, wide=False):
                    if wide:
                        v = u16(at)
                        return (((v & 0x7fff) << 16) | u16(at + 2), at + 4) if v & 0x8000 else (v, at + 2)
                    v = data[at]
                    return (((v & 0x7f) << 8) | data[at + 1], at + 2) if v & 0x80 else (v, at + 1)
                if flags & 0x100:
                    _, cursor = length(cursor)
                    n, cursor = length(cursor)
                    encoding, width = "utf-8", 1
                else:
                    n, cursor = length(cursor, True)
                    encoding, width = "utf-16-le", 2
                if cursor < pos + start or cursor + n * width + width > end:
                    raise ValueError("string outside pool")
                strings.append(data[cursor:cursor + n * width].decode(encoding))
        elif kind == 0x102:
            if header < 16 or size < header + 20:
                raise ValueError("invalid start element")
            ext = pos + header
            name = strings[u32(ext + 4)]
            attr_start, attr_size, count = struct.unpack_from("<HHH", data, ext + 8)
            if attr_start < 20 or attr_size < 20 or ext + attr_start + count * attr_size > end:
                raise ValueError("invalid attributes")
            attrs = {}
            for i in range(count):
                a = ext + attr_start + i * attr_size
                ns, key, raw = struct.unpack_from("<III", data, a)
                typ, value = data[a + 15], u32(a + 16)
                key = strings[key]
                if ns != 0xffffffff:
                    key = "{" + strings[ns] + "}" + key
                if raw != 0xffffffff:
                    value = strings[raw]
                elif typ == 3:
                    value = strings[value]
                elif typ == 0x12:
                    value = "true" if value else "false"
                elif typ in (1, 2):
                    value = f"@0x{value:08x}"
                else:
                    value = str(value)
                attrs[key] = value
            element = ET.Element(name, attrs)
            if stack:
                stack[-1].append(element)
            elif root is None:
                root = element
            else:
                raise ValueError("multiple roots")
            stack.append(element)
        elif kind == 0x103:
            if not stack or size < header + 8 or stack[-1].tag != strings[u32(pos + header + 4)]:
                raise ValueError("unbalanced element")
            stack.pop()
        pos = end
    if root is None or stack or root.tag != "manifest":
        raise ValueError("missing or unbalanced manifest")
    return root


def metadata(root: ET.Element) -> dict:
    def android(e, key, default=""):
        return e.get("{" + ANDROID + "}" + key, default)
    app = root.find("application")
    sdk = root.find("uses-sdk")
    result = {"package": root.get("package", ""), "split": root.get("split", ""),
              "version_name": android(root, "versionName"),
              "version_code": android(root, "versionCode"),
              "min_sdk": android(sdk, "minSdkVersion") if sdk is not None else "",
              "target_sdk": android(sdk, "targetSdkVersion") if sdk is not None else "",
              "label": android(app, "label") if app is not None else "",
              "permissions": [android(e, "name") for e in root if e.tag.startswith("uses-permission")],
              "features": [android(e, "name") for e in root.findall("uses-feature")],
              "components": []}
    if app is not None:
        result["components"] = [{"type": e.tag, "name": android(e, "name")}
                                for e in app if e.tag in ("activity", "activity-alias", "service", "receiver", "provider")]
    return result
