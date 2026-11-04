"""Recover browser entry points; never translate or simulate Android APIs."""
from html import escape
from pathlib import PurePosixPath
import re
from urllib.parse import quote
from .archive import ConversionError, safe_name

GENERATED_ENTRY = "apk2ipk-launch.html"
TEXT_LIMIT = 4 * 1024 * 1024


def html_dependency(text):
    reasons = []
    if re.search(r"<<\s*[A-Za-z_]\w*\s*>>", text):
        reasons.append("Contains template placeholders that Android must replace")
    if re.search(r"\bYouTubePlayerBridge\b|\bYouTubePlayerCallbacks\b", text):
        reasons.append("Uses the Android YouTube player callback bridge")
    return reasons


def mount_ids(text):
    patterns = [r'getElementById\(\s*[\"\']([A-Za-z][\w-]*)[\"\']',
                r'(?:querySelector|\.mount)\(\s*[\"\']#([A-Za-z][\w-]*)[\"\']']
    return sorted({value for pattern in patterns for value in re.findall(pattern, text)})


def script_candidate(name, data):
    path = PurePosixPath(name)
    if path.suffix.lower() not in (".js", ".mjs") or len(data) > TEXT_LIMIT:
        return False
    text = data.decode("utf-8", errors="replace")
    # Android JS bundles require their native renderer even though they are JS.
    if re.search(r'AppRegistry\.registerComponent|__fbBatchedBridge|require\([\"\']react-native', text):
        return False
    # Library chunks and generic URLs are insufficient evidence of an app entry.
    return bool(re.match(r"^(?:main|app|bundle)(?:[.\-_]|$)", path.stem, re.I)
                and (mount_ids(text) or re.search(r"document\.body\.(?:appendChild|innerHTML|append)", text)))


def discover_entries(files):
    """Return ordinary candidates and dependent HTML components separately."""
    candidates, components = [], []
    for name, data in sorted(files.items()):
        path = PurePosixPath(name)
        if path.suffix.lower() not in (".html", ".htm"):
            continue
        reasons = html_dependency(data.decode("utf-8", errors="replace"))
        record = dict(root=str(path.parent), entry=path.name, path=name, kind="html", generated=False)
        if reasons:
            record.update(kind="native-html-template", dependencies=reasons)
            components.append(record)
        else:
            candidates.append(record)
    html_roots = {c["root"] for c in candidates}
    for name, data in sorted(files.items()):
        path = PurePosixPath(name)
        if str(path.parent) not in html_roots and script_candidate(name, data):
            candidates.append(dict(root=str(path.parent), entry=GENERATED_ENTRY,
                                   path=name, kind="javascript-bootstrap", generated=True,
                                   script=path.name, mount_ids=mount_ids(data.decode("utf-8", errors="replace"))))
    return candidates, components


def bootstrap_html(files, script, title):
    """Create the missing document around a selected browser JS entry."""
    safe_name(script)
    if script not in files or PurePosixPath(script).suffix.lower() not in (".js", ".mjs"):
        raise ConversionError("HTML generation needs an existing browser .js or .mjs entry script in the selected web folder.")
    if len(files[script]) > TEXT_LIMIT:
        raise ConversionError("Automatic HTML generation supports entry scripts up to 4 MiB; supply a complete web export for larger entries.")
    text = files[script].decode("utf-8", errors="replace")
    ids = mount_ids(text)
    module = PurePosixPath(script).suffix.lower() == ".mjs" or bool(re.search(r"(?m)^\s*(?:import\s|export\s)", text))
    styles = sorted(n for n in files if PurePosixPath(n).parent == PurePosixPath(script).parent and n.lower().endswith(".css"))
    def url(path):
        return escape(quote(path, safe="/"), quote=True)
    links = "\n".join(f'  <link rel="stylesheet" href="{url(n)}">' for n in styles)
    mounts = "\n".join(f'  <div id="{escape(i, quote=True)}"></div>' for i in ids)
    script_type = ' type="module"' if module else ""
    document = (f'<!doctype html>\n<html lang="en">\n<head>\n'
                f'  <meta charset="utf-8">\n  <meta name="viewport" content="width=device-width, initial-scale=1">\n'
                f'  <title>{escape(title)}</title>\n{links}\n</head>\n<body>\n{mounts}\n'
                f'  <script{script_type} src="{url(script)}"></script>\n</body>\n</html>\n')
    return document.encode("utf-8"), dict(script=script, mount_ids=ids, styles=styles,
                                         module=module, scope="HTML document only; no Android code translation or native API emulation")
