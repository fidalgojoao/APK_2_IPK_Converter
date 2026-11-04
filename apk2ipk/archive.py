"""Conservative, bounded reads of untrusted APKs and web directories."""
from pathlib import Path, PurePosixPath
import stat
import zipfile


class ConversionError(ValueError):
    """A user-facing input or compatibility failure."""


MAX_FILES = 30000
MAX_FILE = 128 * 1024 * 1024
MAX_TOTAL = 512 * 1024 * 1024
MAX_APK = 512 * 1024 * 1024


def safe_name(name: str) -> str:
    if not name or "\\" in name or ":" in name or any(ord(c) < 32 for c in name):
        raise ConversionError(f"Unsafe member path: {name!r}")
    p = PurePosixPath(name)
    if p.is_absolute() or any(x in ("", ".", "..") for x in name.split("/")):
        raise ConversionError(f"Unsafe member path: {name!r}")
    if any(x.endswith((".", " ")) or x.split(".")[0].upper() in
           {"CON", "PRN", "AUX", "NUL", *[f"COM{i}" for i in range(1, 10)],
            *[f"LPT{i}" for i in range(1, 10)]} for x in p.parts):
        raise ConversionError(f"Nonportable member path: {name!r}")
    return name


class APK:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        if self.path.stat().st_size > MAX_APK:
            raise ConversionError("APK exceeds the 512 MiB input limit.")
        self.zip = zipfile.ZipFile(self.path)
        try:
            self.members = {}
            seen = set()
            total = 0
            infos = self.zip.infolist()
            if len(infos) > MAX_FILES:
                raise ConversionError("Archive has too many members.")
            for info in infos:
                name = safe_name(info.filename.rstrip("/"))
                key = name.casefold()
                if key in seen:
                    raise ConversionError(f"Duplicate/case-colliding member: {name}")
                seen.add(key)
                mode = info.external_attr >> 16
                if stat.S_ISLNK(mode) or info.flag_bits & 1:
                    raise ConversionError(f"Symlink/encrypted member rejected: {name}")
                if info.is_dir():
                    continue
                if info.file_size > MAX_FILE:
                    raise ConversionError(f"Member exceeds 128 MiB: {name}")
                total += info.file_size
                if total > MAX_TOTAL:
                    raise ConversionError("Expanded archive exceeds 512 MiB.")
                self.members[name] = info
            file_keys = {n.casefold() for n in self.members}
            for name in self.members:
                for parent in PurePosixPath(name).parents:
                    if str(parent).casefold() in file_keys:
                        raise ConversionError(f"File/directory collision: {name}")
            if "AndroidManifest.xml" not in self.members:
                raise ConversionError("Not a standalone APK: AndroidManifest.xml is missing. Supply the base APK, not an XAPK/APKS bundle.")
        except Exception:
            self.zip.close()
            raise

    def read(self, name: str, limit: int = MAX_FILE) -> bytes:
        info = self.members[name]
        if info.file_size > limit:
            raise ConversionError(f"Member exceeds read limit: {name}")
        with self.zip.open(info) as stream:
            data = stream.read(limit + 1)
        if len(data) > limit:
            raise ConversionError(f"Expanded member exceeds read limit: {name}")
        return data

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.zip.close()


def read_web_directory(root: Path) -> dict[str, bytes]:
    root = root.resolve(strict=True)
    if not root.is_dir():
        raise ConversionError("Web root must be a directory.")
    files = {}
    seen = set()
    total = 0
    for path in sorted(root.rglob("*")):
        if path.is_symlink() or getattr(path, "is_junction", lambda: False)():
            raise ConversionError(f"Links are not accepted in web roots: {path.name}")
        if not path.resolve().is_relative_to(root):
            raise ConversionError("Web asset escapes selected root.")
        if not path.is_file():
            continue
        name = safe_name(path.relative_to(root).as_posix())
        if name.casefold() in seen:
            raise ConversionError(f"Case-colliding file: {name}")
        seen.add(name.casefold())
        if len(files) >= MAX_FILES or path.stat().st_size > MAX_FILE:
            raise ConversionError("Web directory exceeds file/count limits.")
        with path.open("rb") as stream:
            data = stream.read(MAX_FILE + 1)
        total += len(data)
        if len(data) > MAX_FILE or total > MAX_TOTAL:
            raise ConversionError("Web directory exceeds size limits.")
        files[name] = data
    return files
