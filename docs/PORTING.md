# Preserving behavior on LG webOS

The inspector never decides which of your web features are allowed. It records evidence and packages all selected web assets unchanged, including unknown file types. A native bridge that remains in the exported JavaScript will still need an implementation on the TV. Packaging does not create that implementation.

For each screen and feature, record its trigger, state, API calls, permissions, backend requirements and expected result. Rebuild native UI in a TV-capable web stack. Include focus order, D-pad movement, OK, Back (key code 461), pointer input, text input, safe screen margins and accessibility. Keep this test inventory beside the source port.

| Android dependency | Porting work / validation |
|---|---|
| Activities, fragments, Compose layouts | Rebuild UI and lifecycle behavior; Android layout XML is not HTML |
| JNI libraries, DEX code | Reimplement or rebuild appropriate source; CPU similarity does not provide the Android ABI/runtime |
| Cordova/Capacitor plugins | Implement browser or documented webOS equivalents; preserve real error/unsupported states |
| HTTP calls | Verify TV TLS, CORS, cookies, redirects, OAuth callback routes and server authorization |
| Android storage | Use browser storage or supported webOS storage with quotas and lifecycle tests |
| Media | Verify actual TV codecs, containers, streaming formats, subtitles, seek and DRM licenses |
| Billing / Play Services | Integrate a permitted webOS/backend equivalent; Android authorization cannot be reused automatically |
| Camera, GPS, Bluetooth, sensors | Check actual device hardware and documented APIs; unavailable hardware cannot be synthesized |
| Background services | Design for webOS lifecycle and supported services; Android service classes do not run |
| Luna APIs | Set correct `requiredACG` groups in your web export's `appinfo.json`; metadata is retained |

For Cordova/Capacitor, an extracted index may wait forever for a native readiness event. Change that bootstrapping in your original source/web export, replacing the plugin implementation. The converter intentionally does not inject a fake `deviceready` or make unresolved calls report success.

For apps without bundled HTML, obtain the original project and create a real port. Decompilation can help investigation but does not recover complete original source, build configuration, proprietary services or authorized DRM keys. REA can inspect supplied APK artifacts; it is not an Android-to-webOS compiler.

Test initial launch, navigation, relaunch, background/foreground, network loss, failed authentication, expired tokens, storage full, playback errors and TV restart. Keep `runtime_verified` false until your own acceptance testing is complete. Validate each TV model/webOS version you support.
