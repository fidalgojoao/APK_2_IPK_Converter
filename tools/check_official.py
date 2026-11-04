"""Cross-check builtin IPKs with LG CLI; does not connect to a TV."""
import argparse
from pathlib import Path
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from apk2ipk.convert import convert
from apk2ipk.package import verify_ipk


def check(cli_js):
    sample = Path(__file__).resolve().parents[1] / 'examples/tv-web'
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        result = convert(web_dir=sample, output=root / 'builtin', app_id='com.example.apk2ipk.test', title='APK2IPK Test')
        commands = [
            ['node', str(cli_js), '-i', result['ipk']],
            ['node', str(cli_js), str(root / 'builtin/app'), '-o', str(root / 'official'), '--no-minify'],
        ]
        for command in commands:
            subprocess.run(command, check=True, timeout=120)
        official = next((root / 'official').glob('*.ipk'))
        a, b = verify_ipk(result['ipk']), verify_ipk(official)
        assert a['appinfo'] == b['appinfo'], 'App metadata differs from official package'
        for path in sample.rglob('*'):
            if path.is_file():
                exported = root / 'builtin/app' / path.relative_to(sample)
                assert exported.read_bytes() == path.read_bytes(), 'Web asset changed'
        print('PASS: LG CLI inspected builtin IPK, officially repackaged app, and both packages passed structural verification.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cli-js', type=Path, required=True, help='Path to @webos-tools/cli/bin/ares-package.js')
    check(parser.parse_args().cli_js.resolve(strict=True))
