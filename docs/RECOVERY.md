# Missing HTML entry recovery (0.3.0)

## Version 0.4.0: always-create fallback

When no browser entry is detected, Convert now creates `index.html`, a resource manifest and a content-viewer interface, then builds the IPK. APK files under `assets/` and `res/` are retained byte-for-byte under `apk-content/`. Original file paths remain relative within that tree. Images, media, readable text and HTML components can be browsed with search, category filtering, pagination and D-pad focus. Unknown files remain present with an explanation that they cannot be previewed. Binary Android XML is not presented as decoded UI.

The title and persistent banner explicitly state that this is an **APK content viewer**, not the original Android app. Android classes, native libraries, authentication and backend logic are not translated. Native `.so` files within the resource tree remain inert data. HTML components are rendered in an iframe sandbox so their scripts cannot control the viewer; their Android callbacks remain unavailable. Text is displayed as literal text, never injected as HTML. Media depends on TV codec support. Large text previews are limited to 4096 bytes; original files are retained fully.

The fallback can also wrap a user-supplied non-web directory. Existing input files are preserved in the namespace, so a source file named `index.html` cannot overwrite generated viewer files. Explicit invalid entry filenames and output paths still produce normal input errors. `--require-web-app` disables content-viewer generation for workflows that require a recovered browser application.

The Reezn investigation below remains accurate about native functionality. Version 0.4.0 successfully creates a **content-viewer IPK from that APK**, not a functional port of Reezn.

Creating HTML is useful when an APK already contains code that a browser can execute. It is not a way to turn arbitrary Android bytecode, JNI libraries or native layouts into a functioning web app.

## Recovery paths implemented

- Detect `.html` and `.htm` documents of any name under `assets/` and `res/raw/`.
- Detect likely `app`, `main` or `bundle` browser `.js`/`.mjs` entries with literal DOM mounts or document-body updates when no ordinary HTML candidate exists in that directory.
- Generate `apk2ipk-launch.html` with a title, viewport, DOM mount containers, sibling CSS and a reference to the existing JS entry. Module syntax uses a module script. All original selected assets remain unchanged.
- Record the script, mount IDs, styles and generation scope in `conversion.json`.
- Offer every detected HTML component in the GUI's Advanced picker, including dependent components. Selecting a component explicitly exports it without removing bridge calls or pretending it is the full application.
- Support explicit browser JS entries through Advanced settings or `--bootstrap-script`.

Automatic discovery is a heuristic, not proof of a complete app. Arbitrary chunk-loading/bootstrap configuration, script ordering, build-time environment values and dynamically computed mount names cannot be reconstructed reliably from the current patterns. Browser support and native API implementations still require validation. React Native bundles need a native renderer and are not classified as browser apps solely because their file contains JavaScript.

Example without an HTML file:

```sh
python -m apk2ipk convert --web-dir examples/no-index-web --id org.example.recovered --title "Recovered browser app" --output recovered-demo
```

Explicit entry script, relative to the selected web root:

```sh
python -m apk2ipk convert app.apk --asset-root assets/site --bootstrap-script custom.js --id org.example.app --title "My App" --output recovered-app
```

The generated entry must be at the web folder root, and an existing asset is never overwritten. It does not synthesize Android callbacks, readiness events, successful API responses or backend sessions.

## Reezn 2.0.20 investigation

Inspected local artifact: `Reezn v2.0.20.apk`.
SHA-256: `0b4a21911bd7b6b4967915a47d1cb5906358e3098433216272d99b1a0dc2e64b`.
Android package: `com.rmedia.rplayer`.

Observed APK contents:

- `classes.dex` (20,510,723 bytes).
- Android activities for the main screen, login/sign-up, search, video details, playback, downloads, profiles and other features, declared in the manifest.
- Eight native libraries under `lib/`, including `libreezn.so` and `libffmpegJNI.so` across four architectures; four additional `.so` files under `assets/`.
- No HTML or browser JavaScript app entry under `assets/`.
- One HTML file: `res/raw/ayp_youtube_player.html` (5,360 bytes).

The HTML file is an Android-integrated YouTube player template. It contains `<<injectedPlayerVars>>` and `<<injectedVideoId>>` placeholders and invokes `YouTubePlayerBridge` and `YouTubePlayerCallbacks`. Packaging it alone does not implement Reezn's catalog, authentication, source selection, playback orchestration, downloads or other screens. Generating a generic HTML document cannot replace those native implementations.

REA independently identified the APK and inventoried its archive. Summary Evidence ID: `ev_619c6e71ba33c30254ec5a889075d958f72c92bc018098ddbccd4b640e921114`; parent inspection: `ev_b9db9a3d17ff7dd9f95a50e881b73e345baa81e000b21e66e456ef9718662c59`. It reported complete container-entry coverage within its scope and no integrity contradictions. Archive inventory does not establish runtime behavior or signature authenticity.

REA Android decompilation was unavailable because its adapter expected engine 0.7.1 but the installed JAR reported 0.8.0. No configuration was changed. Manifest decoding, archive listing and reading the helper HTML were performed with the toolkit/local Python as separate static evidence. No APK code was executed and no application API was called. The REA session was closed after inspection.

**Outcome:** entry recovery is implemented for supported browser apps, but this is not a working Reezn port. Reezn requires a separate implementation of its UI and logic against supported, authorized services, or an Android device/runtime to execute its existing APK. No Reezn app parity or TV runtime behavior has been verified.
