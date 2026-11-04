from pathlib import Path
import tempfile
import unittest

try:
    from apk2ipk.gui import next_output, suggested_settings
    HAS_TK = True
except ImportError:
    HAS_TK = False


@unittest.skipUnless(HAS_TK, "Tk module not installed")
class DefaultsTests(unittest.TestCase):
    def report(self, **metadata):
        return dict(manifest=dict(package="com.example.app", label="@0x123", version_name="02.3") | metadata,
                    sha256="a" * 64, web_candidates=[dict(root="assets/help", entry="index.html"), dict(root="assets/www", entry="index.html")])

    def test_auto_metadata(self):
        result = suggested_settings("My App.apk", self.report())
        self.assertEqual(result["title"], "My App")
        self.assertEqual(result["version"], "2.3.0")
        self.assertEqual(result["asset_root"], "assets/www")
        self.assertTrue(result["app_id"].startswith("org.apk2ipk.app"))

    def test_identity_stable_across_versions(self):
        a = self.report()
        b = self.report(version_name="3.0.0")
        b["sha256"] = "b" * 64
        self.assertEqual(suggested_settings("a.apk", a)["app_id"], suggested_settings("a.apk", b)["app_id"])

    def test_unusual_label_and_version(self):
        result = suggested_settings("App.apk", self.report(label="App\nTitle", version_name="beta"))
        self.assertEqual(result["title"], "AppTitle")
        self.assertEqual(result["version"], "1.0.0")

    def test_outputs_do_not_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "Sample.apk"
            self.assertEqual(next_output(source).name, "Sample-webos")
            next_output(source).mkdir()
            self.assertEqual(next_output(source).name, "Sample-webos-2")
