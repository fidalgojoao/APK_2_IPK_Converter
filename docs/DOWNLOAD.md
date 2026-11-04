# APK2IPK Studio for Windows

Current application version: **0.4.0** (shown in the window title).

Download **APK2IPK-Studio-0.4.0.exe** from the assets below and double-click it. Close any older copy first. The window title must show **0.4.0**. No installation, Python or terminal commands are required. This download targets Windows x64. Versioned filenames distinguish the fixed executable from earlier files in your Downloads folder; each future release also publishes its own versioned filename and checksum.

1. Click **Choose APK…** and select your Android app file.
2. Let the app fill in the name and output folder. You can change either.
3. Click **Convert to IPK**.
4. Click **Open output folder** to find the `.ipk` file.

Advanced settings are optional. The executable includes its Python and Tk runtimes. It runs locally and does not upload your APK.

Version 0.3.0 also detects HTML pages with other names, pages under `res/raw`, and supported browser JavaScript bundles without an HTML entry. For those bundles it automatically generates an entry HTML page. Advanced settings includes a picker for all detected pages/components and an optional browser JS entry.

Version 0.4.0 adds an automatic fallback: if no browser app is recovered, **Convert to IPK** generates `index.html` and a searchable APK content viewer. It can preview supported images, audio/video, text and HTML components, and retains the resource files. Its title and page explicitly identify it as a content viewer.

This does **not** convert native Android code into JavaScript. Reezn 2.0.20 now produces a content-viewer IPK, but that viewer does not implement Reezn's original catalog, accounts, playback sources or other Android functionality.

Conversion packages reusable web files. Native Android screens and APIs require a webOS-compatible version; the app explains this if it cannot create a useful package. Inspector findings never disable features. Creating an IPK does not verify functionality on a TV.

This is an unsigned executable. The direct download is updated after a successful Windows executable build and automated GUI conversion test.
