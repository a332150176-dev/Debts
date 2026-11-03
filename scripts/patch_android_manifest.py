#!/usr/bin/env python3
"""Add Android's exact-alarm permission for scheduled local debt reminders."""
from pathlib import Path

manifest = Path("android/app/src/main/AndroidManifest.xml")
if not manifest.exists():
    raise SystemExit(f"Android manifest not found: {manifest}")

text = manifest.read_text(encoding="utf-8")
permission = '    <uses-permission android:name="android.permission.SCHEDULE_EXACT_ALARM" />'

if permission.strip() not in text:
    marker = "<application"
    if marker not in text:
        raise SystemExit("Could not find <application> in AndroidManifest.xml")
    text = text.replace(marker, permission + "\n    " + marker, 1)
    manifest.write_text(text, encoding="utf-8")

print("Android exact-alarm permission is present.")
