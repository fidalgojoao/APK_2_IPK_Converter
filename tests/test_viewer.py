from pathlib import Path
import json
import tempfile
import unittest
import zipfile
from apk2ipk.convert import convert
from apk2ipk.package import verify_ipk, icon_png
from apk2ipk.viewer import create_content_viewer, content_kind, NOTICE


class ContentViewerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def test_native_apk_creates_real_index_and_ipk(self):
        apk = self.root / "Native App.apk"
        with zipfile.ZipFile(apk, "w") as z:
            z.writestr("AndroidManifest.xml", '<manifest package="org.example.native"><application/></manifest>')
            z.writestr("classes.dex", b"native code")
            z.writestr("res/drawable/picture.png", icon_png())
            z.writestr("assets/note.txt", b"content to view")
            z.writestr("assets/native.so", b"native data")
        result = convert(apk_path=apk, output=self.root / "out", app_id="org.example.content", title="Native App")
        self.assertEqual(result["mode"], "generated-content-viewer")
        self.assertTrue((self.root / "out/app/index.html").exists())
        self.assertTrue((self.root / "out/app/apk-content/res/drawable/picture.png").exists())
        self.assertEqual((self.root / "out/app/apk-content/assets/note.txt").read_bytes(), b"content to view")
        info = verify_ipk(result["ipk"])["appinfo"]
        self.assertEqual(info["main"], "index.html")
        self.assertIn("APK content", info["title"])
        report = json.loads((self.root / "out/conversion.json").read_text())
        self.assertFalse(report["android_code_translated"])
        self.assertFalse(report["html_reconstruction"]["original_android_app_functionality"])
        self.assertFalse((self.root / "out/app/classes.dex").exists())

    def test_empty_native_apk_still_has_honest_viewer(self):
        files, evidence = create_content_viewer({}, "Empty")
        self.assertIn("index.html", files)
        self.assertIn(NOTICE.encode(), files["index.html"])
        self.assertEqual(evidence["source_file_count"], 0)

    def test_sources_are_preserved_in_namespace(self):
        source = {"index.html": b"<<nativeTemplate>>", "_apk2ipk/viewer.js": b"original", "data.bin": b"\x00\xff"}
        files, _ = create_content_viewer(source, "Test")
        for name, value in source.items():
            self.assertEqual(files["apk-content/" + name], value)

    def test_native_xml_is_not_called_readable_text(self):
        self.assertEqual(content_kind("layout.xml", b"\x03\x00\x08\x00"), "file")
        self.assertEqual(content_kind("layout.xml", b"<layout/>"), "text")

    def test_labels_and_names_are_not_injected_into_html(self):
        files, _ = create_content_viewer({"a #name.txt": b"<script>evil()</script>"}, "<script>title()</script>")
        html = files["index.html"].decode()
        self.assertNotIn("<script>title()", html)
        data = json.loads(files["_apk2ipk/content.json"])
        self.assertEqual(data["items"][0]["path"], "apk-content/a%20%23name.txt")
        self.assertEqual(data["items"][0]["preview"], "<script>evil()</script>")
        self.assertNotIn(b"innerHTML", files["_apk2ipk/viewer.js"])

    def test_large_text_preview_is_bounded_and_full_file_retained(self):
        files, evidence = create_content_viewer({"large.txt": b"x" * 9000}, "Test")
        item = json.loads(files["_apk2ipk/content.json"])["items"][0]
        self.assertEqual(len(item["preview"]), 4096)
        self.assertTrue(item["truncated"])
        self.assertEqual(len(files["apk-content/large.txt"]), 9000)

    def test_external_non_web_files_get_viewer(self):
        web = self.root / "files"
        web.mkdir()
        (web / "readme.txt").write_text("hello")
        result = convert(web_dir=web, output=self.root / "out", app_id="org.example.content", title="Files")
        self.assertEqual(result["mode"], "generated-content-viewer")
        self.assertTrue(verify_ipk(result["ipk"])["valid_structure"])

    def test_binary_xml_and_generated_manifest_are_not_bridge_evidence(self):
        from apk2ipk.analyze import scan_web
        files = {"apk-content/res/layout/a.xml": b'\x03\x00\x08\x00Android.anything https://schema',
                 "_apk2ipk/content.json": b'{"nativeText":"Android.bridge()"}'}
        self.assertEqual(scan_web(files), [])

    def test_fallback_is_independent_of_app_name_and_native_framework(self):
        cases = [("org.sample.notes", "Notes", "lib/arm64-v8a/libflutter.so"),
                 ("com.example.game", "Game", "lib/armeabi-v7a/libunity.so"),
                 ("net.anycompany.tool", "Unknown Tool", "lib/x86_64/libcustom.so")]
        for index, (package, title, library) in enumerate(cases):
            with self.subTest(package=package):
                apk = self.root / f"application-{index}.apk"
                with zipfile.ZipFile(apk, "w") as archive:
                    archive.writestr("AndroidManifest.xml", f'<manifest package="{package}"><application/></manifest>')
                    archive.writestr("classes.dex", b"native code")
                    archive.writestr(library, b"native library")
                    archive.writestr("assets/readme.txt", title)
                result = convert(apk_path=apk, output=self.root / f"out-{index}", app_id=f"org.test.app{index}", title=title)
                self.assertEqual(result["mode"], "generated-content-viewer")
                self.assertEqual(verify_ipk(result["ipk"])["appinfo"]["main"], "index.html")
