# APK → IPK · LG webOS Studio

An offline desktop app and command-line toolkit for inspecting Android APKs, preserving reusable web assets, and packaging web apps for LG webOS TV. Python 3.11+; no third-party runtime dependencies, Android SDK, Java, cloud service or API key required. The desktop UI additionally needs Tk.

**This is an assisted web-app porting tool, not a universal Android emulator or native-code translator.** Native Android UI, DEX, JNI libraries, Google Play Services and Android APIs cannot execute on an LG webOS TV simply by changing their container. Full behavior parity requires source-level porting and testing on the target TV. A generated IPK means a web app was packaged, not that the original Android app has been reproduced.

**Inspector findings never block features.** Scripts, bridge calls, media, arbitrary file types and other assets inside your selected web root are copied without feature filtering or code rewriting. Dependencies are reported so you can implement/test them. No acknowledgement gate is required. Files outside that selected root are not copied. `appinfo.json` receives your explicit webOS identity/entry fields and defaults; other metadata from an existing web export is retained.

## Start

**Windows, no coding required:** [Download APK2IPK-Studio.exe](https://github.com/fidalgojoao/APK_2_IPK_Converter/releases/download/desktop-latest/APK2IPK-Studio.exe), double-click it, click **Choose APK…**, then **Convert to IPK**. The app fills in the technical settings and save location automatically. Click **Open output folder** when finished. Python and Tk are bundled in this executable. See [download instructions](docs/DOWNLOAD.md).

To run from source instead:

```sh
git clone https://github.com/fidalgojoao/APK_2_IPK_Converter.git
cd APK_2_IPK_Converter
python -m apk2ipk gui
```

Or double-click `launch.py` on a Python/Tk installation. On Debian/Ubuntu, install your distribution's `python3-tk` if Tk is absent. Optional installation: `python -m pip install .`, then `apk2ipk gui`. No installation is needed when running from the checkout. On some systems use `python3` instead of `python`.

1. Click **Choose APK…**. The app reads it automatically and fills in the settings.
2. Optionally change the TV app name and save location. Additional options are under **Advanced settings**.
3. Click **Convert to IPK**, then **Open output folder**.
4. Install/test the IPK on your TV. Native Android apps require a source port; an already rebuilt web folder can be selected under **Advanced settings**.

## CLI

Inspect without executing APK code:

```sh
python -m apk2ipk analyze application.apk --output apk-report
python -m apk2ipk analyze application.apk --json
```

Package the web root inside an APK (single root is selected automatically):

```sh
python -m apk2ipk convert application.apk --asset-root assets/www --id com.yourcompany.tvapp --title "My TV App" --output webos-build
```

Package a web export rebuilt from source:

```sh
python -m apk2ipk convert --web-dir path/to/web-export --id com.yourcompany.tvapp --title "My TV App" --app-version 1.2.0 --entry index.html --output webos-build
python -m apk2ipk verify webos-build/com.yourcompany.tvapp_1.2.0_all.ipk
```

Use `--project-only` to generate an editable webOS project without an IPK. After editing `webos-build/app`, package that directory with LG's CLI, or run `convert --web-dir webos-build/app` into a **new** output directory. Output directories are never overwritten. All commands return exit code 2 for invalid inputs; success returns 0. `--acknowledge-limitations` is optional and records an acknowledgement only.

## What you get

| Output | Purpose |
|---|---|
| `app/` | Editable selected web assets and webOS `appinfo.json` |
| `<id>_<version>_all.ipk` | Deterministic ar/gzip/tar webOS web-app package |
| `analysis/report.json`, `analysis/REPORT.md` | APK identity, manifest declarations, web candidates and dependency evidence (when an APK was supplied) |
| `conversion.json` | Source asset hashes, preserved dependency findings and explicit scope |
| `verification.json` | Package structure and entry/metadata checks |
| `TESTING.md` | TV acceptance checklist |

The built-in packager supplies a placeholder 80×80 PNG if your web export has no icon. Supply a PNG and reference it from the web export's `appinfo.json` for your own artwork. Versions require three numbers, such as `1.0.0`. Existing optional webOS metadata is retained, including `requiredACG`; the default is `[]`. Declare the actual access control groups needed by your port's Luna calls. Android permissions are never converted into webOS grants.

## Supported paths and limits

| APK content | Practical path |
|---|---|
| Standalone HTML/CSS/JS app in `assets/` | Export all selected assets, package, test |
| Cordova / Capacitor | Preserve assets and calls; replace native plugins for webOS/browser APIs |
| Native Android / Jetpack Compose / React Native | Port original source and supply a web export |
| Flutter / Unity | Rebuild an appropriate target from original source; supply a compatible web export to this tool |
| DRM, billing, Google services, hardware, background services | Implement supported equivalents; verify service authorization and TV support |
| Split APK, AAB, APKS, XAPK | Supply a standalone/base APK and complete web export; split assembly is not implemented |

Analysis reads plain/binary Android XML (UTF-8/UTF-16 string pools), components, SDK declarations, permissions, library names and selected web text. Findings are heuristics; dynamically constructed APIs, obfuscation and code paths may be missed. It does not decompile DEX or resolve `resources.arsc`. HTML candidates are not proof of standalone functionality. It never fakes successful native plugin/API calls.

Inputs are local. No APK code is executed; no remote app URLs are fetched. Archive integrity/path rules reject traversal, duplicate/case-colliding paths, encrypted members, links and oversized inputs. These are input integrity checks, not feature policies. Default limits: 512 MiB APK/expanded content, 128 MiB per file, 30,000 ZIP members; heuristic text scanning covers files up to 4 MiB each. Use a dedicated exported web directory, as every file inside it will enter the package.

## LG tooling and deployment

The builtin IPK format is cross-checked against `@webos-tools/cli@3.2.6`. For official repackaging and deployment, install [LG's CLI](https://github.com/webos-tools/cli) and follow the [LG Developer Mode setup](https://webostv.developer.lge.com/develop/getting-started/build-your-first-web-app):

```sh
ares-package webos-build/app -o official-package --no-minify
ares-package -i official-package/com.yourcompany.tvapp_1.2.0_all.ipk
ares-install --device myTV official-package/com.yourcompany.tvapp_1.2.0_all.ipk
ares-launch --device myTV com.yourcompany.tvapp
```

Configure `myTV` first with LG's device setup workflow. This toolkit does not connect to your TV automatically. Package inspection is structural validation; model-specific browser APIs, video codecs, remote focus, lifecycle, authentication and DRM must be tested on-device. LG Store acceptance/signing is a separate process.

## Demo and checks

The included TV web app has keyboard/remote navigation and a local-storage test:

```sh
python -m apk2ipk convert --web-dir examples/tv-web --id com.example.apk2ipk.demo --title "APK2IPK TV Demo" --output demo-build
python -m unittest discover -s tests -v
```

`tools/make_demo_apk.py demo.apk` creates an unsigned, APK-shaped test fixture from the demo assets. It is **not installable on Android** and is not evidence of real Android application parity.

GitHub Actions runs tests on Windows/macOS/Linux and Python 3.11/3.13, cross-checks the packager with LG's CLI, and uploads the demo project/IPK. The manually dispatched **Build desktop executables** workflow bundles the GUI with PyInstaller and uploads platform-specific executables. These builds are unsigned; GUI bundling is separate from APK conversion.

## REA and Graphify

Development used REA to independently inventory the synthetic APK fixture and Graphify to index/query implementation relationships. The converter itself does not require these development tools. See [validation evidence](docs/VALIDATION.md), [porting guide](docs/PORTING.md) and [architecture](docs/ARCHITECTURE.md). Committed `graphify-out/` outputs are the code graph/report/viewer; local machine-specific caches are ignored.

Official references: [Android application fundamentals](https://developer.android.com/guide/components/fundamentals), [webOS app metadata](https://webostv.developer.lge.com/develop/references/appinfo-json), [LG CLI guide](https://webostv.developer.lge.com/develop/tools/cli-dev-guide), [webOS access control groups](https://webostv.developer.lge.com/develop/guides/acg-guide).
