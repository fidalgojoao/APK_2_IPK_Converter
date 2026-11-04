"""Generate an unsigned APK-shaped test archive. Not installable on Android."""
from pathlib import Path
import argparse
import zipfile

MANIFEST = '''<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="com.example.demo" android:versionName="1.0.0"><uses-sdk android:minSdkVersion="23" android:targetSdkVersion="35"/><application android:label="TV web fixture"><activity android:name=".MainActivity"/></application></manifest>'''


def create(output):
    root = Path(__file__).resolve().parents[1] / "examples" / "tv-web"
    with zipfile.ZipFile(output, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("AndroidManifest.xml", MANIFEST)
        for path in sorted(root.iterdir()):
            archive.write(path, "assets/www/" + path.name)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("output", type=Path)
    create(p.parse_args().output)
