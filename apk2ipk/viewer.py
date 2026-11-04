"""Generate an honest, offline content viewer when no web app is recoverable."""
from html import escape
import json
from pathlib import PurePosixPath
from urllib.parse import quote

NOTICE = "APK content viewer — the original Android app has not been converted. Android screens, APIs, accounts and native code do not run here."


def content_kind(name, data):
    suffix = PurePosixPath(name).suffix.lower()
    if suffix in (".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg", ".bmp"):
        return "image"
    if suffix in (".mp4", ".webm", ".m4v", ".mov", ".mkv"):
        return "video"
    if suffix in (".mp3", ".ogg", ".wav", ".m4a", ".aac", ".flac"):
        return "audio"
    if suffix in (".html", ".htm"):
        return "html"
    if suffix in (".txt", ".json", ".js", ".mjs", ".css", ".csv", ".xml", ".md", ".glsl", ".m3u", ".m3u8"):
        try:
            sample = data[:4096].decode("utf-8")
            if not any(ord(c) < 32 and c not in "\n\r\t" for c in sample):
                return "text"
        except UnicodeDecodeError:
            pass
    return "file"


def create_content_viewer(source_files, title):
    files, items = {}, []
    for name, data in sorted(source_files.items()):
        path = "apk-content/" + name
        files[path] = data
        kind = content_kind(name, data)
        record = dict(name=name, path=quote(path, safe="/"), kind=kind, size=len(data))
        if kind == "text":
            record["preview"] = data[:4096].decode("utf-8", errors="replace")
            record["truncated"] = len(data) > 4096
        items.append(record)
    payload = dict(title=title, notice=NOTICE, items=items)
    files["_apk2ipk/viewer.js"] = ("var APK_CONTENT = " + json.dumps(payload, ensure_ascii=True) + ";\n" + VIEWER_JS).encode()
    files["_apk2ipk/viewer.css"] = VIEWER_CSS.encode()
    files["_apk2ipk/content.json"] = json.dumps(payload, indent=2, ensure_ascii=True).encode()
    html = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(title)} — APK content viewer</title>
<link rel="stylesheet" href="_apk2ipk/viewer.css"></head><body>
<header><p class="eyebrow">APK2IPK / CONTENT VIEWER</p><h1 id="title"></h1>
<p class="notice">{escape(NOTICE)}</p></header>
<main><section class="toolbar"><label>Search files <input id="search" type="search" placeholder="Type a file name"></label>
<label>Show <select id="filter"><option value="all">All files</option><option value="image">Images</option><option value="video">Video</option><option value="audio">Audio</option><option value="text">Text</option><option value="html">HTML components</option><option value="file">Other files</option></select></label>
<button id="previous">Previous page</button><button id="next">Next page</button></section>
<p id="count" role="status" aria-live="polite"></p>
<div class="columns"><section id="files" aria-label="Files"></section>
<section id="preview" aria-label="File preview"><h2>Choose a file</h2><p>Use your remote arrows and OK. Media playback depends on your TV's codecs. HTML components may require Android integration.</p></section></div></main>
<script src="_apk2ipk/viewer.js"></script></body></html>'''
    files["index.html"] = html.encode()
    counts = {kind: sum(i["kind"] == kind for i in items) for kind in ("image", "audio", "video", "text", "html", "file")}
    return files, dict(mode="generated-content-viewer", entry="index.html", counts=counts,
                       source_file_count=len(items), notice=NOTICE,
                       original_android_app_functionality=False)


VIEWER_JS = r'''(function () {
  'use strict';
  var data = APK_CONTENT;
  var page = 0, pageSize = 20;
  var files = document.getElementById('files');
  var preview = document.getElementById('preview');
  var search = document.getElementById('search');
  var filter = document.getElementById('filter');
  var previous = document.getElementById('previous');
  var next = document.getElementById('next');
  document.getElementById('title').textContent = data.title + ' — APK content';
  function empty(element) { while (element.firstChild) { element.removeChild(element.firstChild); } }
  function add(parent, tag, text) {
    var node = document.createElement(tag);
    if (text !== undefined) { node.textContent = text; }
    parent.appendChild(node); return node;
  }
  function show(item) {
    empty(preview);
    add(preview, 'h2', item.name);
    add(preview, 'p', item.kind + ' · ' + item.size + ' bytes');
    if (item.kind === 'image') {
      var image = add(preview, 'img'); image.alt = item.name; image.src = item.path;
      image.onerror = function () { add(preview, 'p', 'This image format could not be displayed.'); };
    } else if (item.kind === 'audio' || item.kind === 'video') {
      var media = add(preview, item.kind); media.controls = true; media.preload = 'metadata'; media.src = item.path;
      media.onerror = function () { add(preview, 'p', 'This media cannot be played by this browser/TV.'); };
    } else if (item.kind === 'text') {
      add(preview, 'pre', item.preview + (item.truncated ? '\n\n[Preview limited to 4096 bytes; full file retained.]' : ''));
    } else if (item.kind === 'html') {
      add(preview, 'p', 'Embedded HTML component. Android callbacks and injected data are unavailable. This is not the full Android application.');
      var frame = add(preview, 'iframe'); frame.title = item.name;
      frame.setAttribute('sandbox', 'allow-scripts'); frame.src = item.path;
    } else {
      add(preview, 'p', 'File retained. This browser cannot preview this format. Native Android code is not executable here.');
    }
  }
  function render() {
    var query = search.value.toLowerCase();
    var selected = data.items.filter(function (i) { return i.name.toLowerCase().indexOf(query) !== -1 && (filter.value === 'all' || i.kind === filter.value); });
    var last = Math.max(0, Math.ceil(selected.length / pageSize) - 1);
    page = Math.min(page, last);
    empty(files);
    selected.slice(page * pageSize, (page + 1) * pageSize).forEach(function (item) {
      var button = add(files, 'button', '[' + item.kind + '] ' + item.name);
      button.onclick = function () { show(item); };
    });
    if (!selected.length) { add(files, 'p', 'No matching files. This APK may contain only native code/data.'); }
    document.getElementById('count').textContent = selected.length + ' files · Page ' + (page + 1) + ' of ' + (last + 1);
    previous.disabled = page === 0; next.disabled = page === last;
  }
  search.oninput = filter.onchange = function () { page = 0; render(); };
  previous.onclick = function () { page = Math.max(0, page - 1); render(); };
  next.onclick = function () { page += 1; render(); };
  document.addEventListener('keydown', function (event) {
    var active = document.activeElement;
    if (active && /TEXTAREA|VIDEO|AUDIO|IFRAME/.test(active.tagName)) { return; }
    if (active && active.tagName === 'INPUT' && (event.keyCode === 37 || event.keyCode === 39)) { return; }
    if (active && active.tagName === 'SELECT' && (event.keyCode === 38 || event.keyCode === 40)) { return; }
    if (event.keyCode >= 37 && event.keyCode <= 40) {
      var nodes = Array.prototype.slice.call(document.querySelectorAll('button:not([disabled]), input, select'));
      var index = nodes.indexOf(active);
      index = (index + (event.keyCode === 37 || event.keyCode === 38 ? -1 : 1) + nodes.length) % nodes.length;
      if (nodes[index]) { nodes[index].focus(); event.preventDefault(); }
    }
  });
  render(); search.focus();
}());'''

VIEWER_CSS = '''html{background:#101820;color:#e8f2f5;font:22px Arial,sans-serif}body{margin:0;padding:3vh 4vw}h1{font-size:40px;margin:12px 0}.eyebrow{color:#42dec1;letter-spacing:.12em;font-size:17px}.notice{background:#293747;padding:15px;border-left:4px solid #42dec1;line-height:1.4}.toolbar{display:flex;gap:16px;align-items:end;flex-wrap:wrap}label{display:block}input,select,button{font:inherit;padding:12px;background:#203444;color:white;border:3px solid transparent;border-radius:7px}input,select{display:block}button:focus,input:focus,select:focus{border-color:#42dec1;outline:0}button:disabled{opacity:.4}.columns{display:grid;grid-template-columns:45% 53%;gap:2%}#files{max-height:58vh;overflow:auto}#files button{display:block;width:100%;text-align:left;margin:0 0 8px;overflow-wrap:anywhere}#preview{padding:16px;background:#192733;max-height:58vh;overflow:auto}#preview h2{font-size:24px;overflow-wrap:anywhere}img,video,iframe{max-width:100%;max-height:40vh}iframe{width:100%;height:35vh;border:0;background:white}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:18px}'''
