from pathlib import Path
import contextlib
import io
import json
import struct
import tempfile
import unittest
import zipfile
from apk2ipk.analyze import inspect_apk, scan_web
from apk2ipk.archive import APK, ConversionError, safe_name, read_web_directory
from apk2ipk.cli import main
from apk2ipk.convert import convert
from apk2ipk.manifest import parse_manifest, metadata
from apk2ipk.package import make_ipk, verify_ipk, icon_png, validate_metadata

XML = b'<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="com.example.a" android:versionName="2.3"><uses-permission android:name="android.permission.CAMERA"/><application android:label="App"><activity android:name=".Main"/></application></manifest>'


def binary_manifest(utf8=True):
    strings = ["manifest", "package", "com.example.binary", "application", "label", "Binary App", "http://schemas.android.com/apk/res/android"]
    encoded = []
    offsets = []
    for s in strings:
        offsets.append(sum(map(len, encoded)))
        raw = s.encode("utf-8" if utf8 else "utf-16-le")
        encoded.append(bytes([len(s), len(raw)]) + raw + b'\0' if utf8 else struct.pack('<H', len(s)) + raw + b'\0\0')
    body = b''.join(encoded)
    body += b'\0' * (-len(body) % 4)
    pool_size = 28 + 4 * len(strings) + len(body)
    pool = struct.pack('<HHIIIIII', 1, 28, pool_size, len(strings), 0, 0x100 if utf8 else 0, 28 + 4 * len(strings), 0) + struct.pack('<' + 'I' * len(offsets), *offsets) + body
    def start(name, key, value, ns=0xffffffff):
        attr = struct.pack('<IIIHBBI', ns, key, 0xffffffff, 8, 0, 3, value)
        return struct.pack('<HHIII', 0x102, 16, 56, 1, 0xffffffff) + struct.pack('<IIHHHHHH', 0xffffffff, name, 20, 20, 1, 0, 0, 0) + attr
    def end(name):
        return struct.pack('<HHIIIII', 0x103, 16, 24, 1, 0xffffffff, 0xffffffff, name)
    body = pool + start(0, 1, 2) + start(3, 4, 5, 6) + end(3) + end(0)
    return struct.pack('<HHI', 3, 8, len(body) + 8) + body


class ConverterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.apk = self.root / 'test.apk'

    def fixture(self, extra=None, manifest=XML):
        with zipfile.ZipFile(self.apk, 'w') as z:
            z.writestr('AndroidManifest.xml', manifest)
            for name, data in (extra or {}).items():
                z.writestr(name, data)
        return self.apk

    def build(self, **kw):
        args = dict(apk_path=self.apk, output=self.root / 'out', app_id='com.example.tv', title='TV App', acknowledge=True)
        args.update(kw)
        return convert(**args)

    def test_manifest_plain(self):
        m = metadata(parse_manifest(XML))
        self.assertEqual(m['package'], 'com.example.a')
        self.assertEqual(m['permissions'], ['android.permission.CAMERA'])
        self.assertEqual(m['components'][0]['name'], '.Main')

    def test_manifest_binary_both_string_encodings(self):
        for encoding in (True, False):
            m = metadata(parse_manifest(binary_manifest(encoding)))
            self.assertEqual(m['package'], 'com.example.binary')
            self.assertEqual(m['label'], 'Binary App')

    def test_bad_binary_manifest(self):
        for data in (b'', b'\x03\0\x08\0\xff\xff\xff\xff', binary_manifest()[:-1]):
            with self.assertRaises(ConversionError):
                parse_manifest(data)

    def test_dtd_and_wrong_root_rejected(self):
        for data in (b'<!DOCTYPE a [<!ENTITY b "x">]><manifest/>', b'<notmanifest/>'):
            with self.assertRaises(ConversionError):
                parse_manifest(data)

    def test_native_requires_port(self):
        self.fixture({'classes.dex': b'dex\n035\0', 'lib/arm64-v8a/libflutter.so': b'ELF'})
        report = inspect_apk(self.apk)
        self.assertEqual(report['status'], 'source-port-required')
        self.assertTrue(report['native_libraries'])
        self.assertIn('flutter', [f['id'] for f in report['findings']])
        with self.assertRaises(ConversionError):
            self.build()
        self.assertFalse((self.root / 'out').exists())

    def test_roundtrip_web_candidate(self):
        self.fixture({'assets/www/index.html': b'<html>Hello</html>', 'classes.dex': b'android code'})
        result = self.build()
        verified = verify_ipk(result['ipk'])
        self.assertTrue(verified['valid_structure'])
        self.assertFalse(verified['runtime_verified'])
        self.assertFalse((self.root / 'out/app/classes.dex').exists())
        self.assertTrue((self.root / 'out/analysis/report.json').exists())
        self.assertTrue((self.root / 'out/conversion.json').exists())

    def test_binary_manifest_end_to_end(self):
        self.fixture({'assets/www/index.html': b'<html/>'}, manifest=binary_manifest())
        self.assertTrue(verify_ipk(self.build()['ipk'])['valid_structure'])

    def test_explicit_root_and_custom_entry(self):
        self.fixture({'assets/site/home.htm': b'<html/>'})
        result = self.build(asset_root='assets/site', entry='home.htm')
        self.assertEqual(verify_ipk(result['ipk'])['appinfo']['main'], 'home.htm')

    def test_multiple_candidates_require_choice(self):
        self.fixture({'assets/a/index.html': b'A', 'assets/b/index.html': b'B'})
        with self.assertRaises(ConversionError):
            self.build()

    def test_no_acknowledgement_required(self):
        self.fixture({'assets/www/index.html': b'<html/>'})
        self.assertTrue(verify_ipk(self.build(acknowledge=False)['ipk'])['valid_structure'])

    def test_findings_never_filter_or_rewrite_features(self):
        source = b'cordova.exec(); Android.anyFeature(); Capacitor.Plugins.Camera(); fetch("https://api.example.com")'
        self.fixture({'assets/www/index.html': b'<script src="bridge.js"></script>', 'assets/www/bridge.js': source, 'assets/www/opaque.custom': b'\x00\xffanything'})
        result = self.build(acknowledge=False)
        self.assertGreaterEqual(len(result['web_findings']), 4)
        self.assertEqual((self.root / 'out/app/bridge.js').read_bytes(), source)
        self.assertEqual((self.root / 'out/app/opaque.custom').read_bytes(), b'\x00\xffanything')

    def test_existing_output_preserved(self):
        self.fixture({'assets/www/index.html': b'<html/>'})
        out = self.root / 'out'
        out.mkdir()
        (out / 'precious').write_text('keep')
        with self.assertRaises(ConversionError):
            self.build()
        self.assertEqual((out / 'precious').read_text(), 'keep')

    def test_external_web_directory(self):
        web = self.root / 'web'
        web.mkdir()
        (web / 'index.html').write_text('<html/>')
        result = self.build(apk_path=None, web_dir=web)
        self.assertTrue(verify_ipk(result['ipk'])['valid_structure'])

    def test_project_only(self):
        self.fixture({'assets/www/index.html': b'<html/>'})
        self.assertIsNone(self.build(project_only=True)['ipk'])
        self.assertTrue((self.root / 'out/app/appinfo.json').exists())

    def test_split_rejected(self):
        self.fixture(manifest=XML.replace(b'package=', b'split="config.en" package='))
        with self.assertRaises(ConversionError):
            inspect_apk(self.apk)

    def test_bundle_without_manifest_rejected(self):
        with zipfile.ZipFile(self.apk, 'w') as z:
            z.writestr('base.apk', b'APK')
        with self.assertRaises(ConversionError):
            APK(self.apk)

    def test_dangerous_paths(self):
        for name in ('../evil', '/etc/a', 'C:/evil', 'a\\b', 'a/./b', 'a//b', 'CON', 'a/NUL.txt', 'a./b'):
            with self.subTest(name=name), self.assertRaises(ConversionError):
                safe_name(name)

    def test_archive_traversal_rejected(self):
        self.fixture({'../outside': b'x'})
        with self.assertRaises(ConversionError):
            inspect_apk(self.apk)

    def test_case_collision_rejected(self):
        self.fixture({'assets/www/a': b'1', 'assets/www/A': b'2'})
        with self.assertRaises(ConversionError):
            inspect_apk(self.apk)

    def test_file_directory_collision_rejected(self):
        self.fixture({'assets/a': b'1', 'assets/a/index.html': b'2'})
        with self.assertRaises(ConversionError):
            inspect_apk(self.apk)

    def test_symlink_rejected(self):
        self.fixture()
        with zipfile.ZipFile(self.apk, 'a') as z:
            info = zipfile.ZipInfo('assets/link')
            info.create_system = 3
            info.external_attr = 0o120777 << 16
            z.writestr(info, '../../outside')
        with self.assertRaises(ConversionError):
            inspect_apk(self.apk)

    def test_declared_limits_enforced(self):
        self.fixture({'assets/large': b'x' * 1024})
        from unittest.mock import patch
        with patch('apk2ipk.archive.MAX_TOTAL', 512), self.assertRaises(ConversionError):
            inspect_apk(self.apk)

    def test_invalid_metadata(self):
        info = dict(id='com.example.tv', title='TV', version='1.0.0', main='index.html', icon='icon.png', type='web')
        for changes in ({'id': 'com.webos.bad'}, {'id': '../evil'}, {'version': '01.0.0'}, {'version': '1.0'}, {'title': 'x\nPackage: evil'}, {'main': '../index.html'}, {'type': 'native'}):
            with self.subTest(changes=changes), self.assertRaises(ConversionError):
                validate_metadata(info | changes)

    def test_ipk_reproducibility(self):
        info = dict(id='com.example.tv', title='TV', version='1.0.0', main='index.html', icon='icon.png', type='web')
        files = {'index.html': b'<html/>', 'icon.png': icon_png()}
        self.assertEqual(make_ipk(files, info), make_ipk(files, info))

    def test_tampered_ipk_rejected(self):
        self.fixture({'assets/www/index.html': b'<html/>'})
        ipk = Path(self.build()['ipk'])
        ipk.write_bytes(ipk.read_bytes()[:-12])
        with self.assertRaises(ConversionError):
            verify_ipk(ipk)

    def test_bridge_findings_have_paths(self):
        findings = scan_web({'index.js': b'cordova.exec(); Android.camera(); fetch("https://api.example.com")'})
        self.assertEqual({f['id'] for f in findings}, {'cordova', 'android-bridge', 'network'})
        self.assertTrue(all(f['evidence'] == ['index.js'] for f in findings))

    def test_cli_workflow(self):
        self.fixture({'assets/www/index.html': b'<html/>'})
        with contextlib.redirect_stdout(io.StringIO()) as stdout:
            self.assertEqual(main(['analyze', str(self.apk), '--json']), 0)
        self.assertEqual(json.loads(stdout.getvalue())['status'], 'web-assets-need-review')
        with contextlib.redirect_stdout(io.StringIO()):
            code = main(['convert', str(self.apk), '--id', 'com.example.tv', '--title', 'TV', '--output', str(self.root / 'out'), '--acknowledge-limitations'])
            self.assertEqual(code, 0)

    def test_cli_malformed_inputs_exit_cleanly(self):
        self.apk.write_bytes(b'not a zip')
        with contextlib.redirect_stderr(io.StringIO()) as stderr:
            self.assertEqual(main(['analyze', str(self.apk)]), 2)
        self.assertIn('apk2ipk:', stderr.getvalue())


if __name__ == '__main__':
    unittest.main()
