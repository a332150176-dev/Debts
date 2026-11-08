#!/usr/bin/env python3
"""Patch generated Android permissions and the app's short launcher label."""
from pathlib import Path
import re

manifest = Path("android/app/src/main/AndroidManifest.xml")
if not manifest.exists():
    raise SystemExit(f"Android manifest not found: {manifest}")

manifest_text = manifest.read_text(encoding="utf-8")
permission = '    <uses-permission android:name="android.permission.SCHEDULE_EXACT_ALARM" />'

if permission.strip() not in manifest_text:
    marker = "<application"
    if marker not in manifest_text:
        raise SystemExit("Could not find <application> in AndroidManifest.xml")
    manifest_text = manifest_text.replace(marker, permission + "\n    " + marker, 1)
    manifest.write_text(manifest_text, encoding="utf-8")

strings_file = Path("android/app/src/main/res/values/strings.xml")
if strings_file.exists():
    strings_text = strings_file.read_text(encoding="utf-8")
    app_name_pattern = r'(<string\s+name="app_name"[^>]*>).*?(</string>)'
    updated, count = re.subn(app_name_pattern, r'\1פנקס\2', strings_text, count=1, flags=re.S)
    if count != 1:
        raise SystemExit("Could not find app_name in Android strings.xml")
    if updated != strings_text:
        strings_file.write_text(updated, encoding="utf-8")
else:
    raise SystemExit(f"Android app strings file not found: {strings_file}")

print("Android exact-alarm permission and launcher label are configured.")
