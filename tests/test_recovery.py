import json
from pathlib import Path
import tempfile
import unittest
import zipfile
from apk2ipk.analyze import inspect_apk
from apk2ipk.archive import ConversionError
from apk2ipk.convert import convert
from apk2ipk.package import verify_ipk
from apk2ipk.recover import bootstrap_html, discover_entries, GENERATED_ENTRY


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.apk = self.root / "test.apk"

    def fixture(self, files):
        with zipfile.ZipFile(self.apk, "w") as z:
            z.writestr("AndroidManifest.xml", '<manifest package="com.example.native"><application/></manifest>')
            for name, data in files.items():
                z.writestr(name, data)

    def build(self, **options):
        args = dict(apk_path=self.apk, output=self.root / "out", app_id="org.example.recovered", title="Recovered App")
        args.update(options)
        return convert(**args)

    def test_non_index_html_is_detected_and_packaged(self):
        self.fixture({"assets/site/start.htm": b"<!doctype html><h1>Working web page</h1>"})
        report = inspect_apk(self.apk)
        self.assertEqual(report["web_candidates"][0]["entry"], "start.htm")
        verified = verify_ipk(self.build()["ipk"])
        self.assertEqual(verified["appinfo"]["main"], "start.htm")

    def test_raw_resource_html_is_detected(self):
        self.fixture({"res/raw/welcome.html": b"<h1>Hello</h1>"})
        self.assertTrue(verify_ipk(self.build()["ipk"])["valid_structure"])

    def test_assets_root_is_supported(self):
        self.fixture({"assets/home.html": b"<h1>Home</h1>"})
        self.assertEqual(inspect_apk(self.apk)["web_candidates"][0]["root"], "assets")
        self.assertTrue(verify_ipk(self.build()["ipk"])["valid_structure"])

    def test_browser_javascript_recovers_without_any_html(self):
        source = b'document.getElementById("app").innerHTML = "<h1>App loaded</h1>";'
        self.fixture({"assets/www/main.js": source, "assets/www/style.css": b"body {color: teal}"})
        candidate = inspect_apk(self.apk)["web_candidates"][0]
        self.assertTrue(candidate["generated"])
        result = self.build()
        out = self.root / "out"
        html = (out / "app" / GENERATED_ENTRY).read_text()
        self.assertIn('<div id="app"></div>', html)
        self.assertIn('src="main.js"', html)
        self.assertIn('href="style.css"', html)
        self.assertEqual((out / "app/main.js").read_bytes(), source)
        provenance = json.loads((out / "conversion.json").read_text())
        self.assertEqual(provenance["html_reconstruction"]["mount_ids"], ["app"])
        self.assertFalse(provenance["android_code_translated"])
        self.assertEqual(verify_ipk(result["ipk"])["appinfo"]["main"], GENERATED_ENTRY)

    def test_external_web_export_missing_html(self):
        web = self.root / "web"
        web.mkdir()
        (web / "app.mjs").write_text('export {}; document.getElementById("root").textContent = "App";')
        self.build(apk_path=None, web_dir=web)
        html = (self.root / "out/app" / GENERATED_ENTRY).read_text()
        self.assertIn('type="module"', html)
        self.assertIn('id="root"', html)

    def test_native_youtube_helper_is_not_misrepresented_as_app(self):
        source = b'<script>var x = <<injectedVideoId>>; YouTubePlayerBridge.sendReady();</script>'
        self.fixture({"res/raw/ayp_youtube_player.html": source, "classes.dex": b"native Android code"})
        report = inspect_apk(self.apk)
        self.assertEqual(report["web_candidates"], [])
        self.assertEqual(len(report["embedded_web_components"]), 1)
        with self.assertRaises(ConversionError):
            self.build(require_web_app=True)
        # An explicit component export is allowed, without modifying native calls.
        result = self.build(asset_root="res/raw", entry="ayp_youtube_player.html")
        self.assertTrue(verify_ipk(result["ipk"])["valid_structure"])
        self.assertEqual((self.root / "out/app/ayp_youtube_player.html").read_bytes(), source)

    def test_react_native_bundle_is_not_browser_code(self):
        candidates, _ = discover_entries({"assets/main.js": b'require("react-native"); AppRegistry.registerComponent("app", function () {}); document.getElementById("root");'})
        self.assertEqual(candidates, [])

    def test_regular_library_is_not_guessed_to_be_an_app(self):
        self.assertEqual(discover_entries({"assets/vendor.js": b'document.getElementById("app");'})[0], [])

    def test_explicit_javascript_entry_and_html_escaping(self):
        self.fixture({"assets/site/custom entry.js": b'document.body.innerHTML = "app";'})
        self.build(asset_root="assets/site", bootstrap_script="custom entry.js", title="<My & App>")
        html = (self.root / "out/app" / GENERATED_ENTRY).read_text()
        self.assertIn("&lt;My &amp; App&gt;", html)
        self.assertIn('src="custom%20entry.js"', html)

    def test_generated_entry_never_overwrites_a_file(self):
        self.fixture({"assets/site/main.js": b'document.getElementById("app");', "assets/site/existing.html": b"keep"})
        with self.assertRaises(ConversionError):
            self.build(asset_root="assets/site", entry="existing.html", bootstrap_script="main.js")

    def test_javascript_source_is_not_changed(self):
        source = b'document.getElementById("app"); Android.someCall(); cordova.exec();'
        files = {"app.js": source}
        html, evidence = bootstrap_html(files, "app.js", "Test")
        self.assertEqual(files["app.js"], source)
        self.assertNotIn(b"cordova", html)
        self.assertEqual(evidence["script"], "app.js")


if __name__ == "__main__":
    unittest.main()
