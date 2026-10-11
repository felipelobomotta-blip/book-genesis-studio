"""Rebuild the data-only timezone archive from a pinned official tzdata wheel.

No package is installed or imported. Only TZif data and original licenses ship.
Download the declared wheel from PyPI, then pass its local path to this script.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import zipfile

VERSION = "2026.5"
WHEEL_SHA256 = "b683bd1b6659ddcd810ff02ad09ba821d4bf1065072805063eb35c49617905ac"
ROOT = Path(__file__).resolve().parents[1]


def build(wheel, destination):
    data = Path(wheel).read_bytes()
    if hashlib.sha256(data).hexdigest() != WHEEL_SHA256:
        raise ValueError("Timezone wheel differs from the pinned official PyPI checksum")
    zones, licenses = {}, {}
    with zipfile.ZipFile(io.BytesIO(data)) as source:
        for name in source.namelist():
            if name.startswith("tzdata/zoneinfo/"):
                raw = source.read(name)
                if raw.startswith(b"TZif"):
                    zones[name.removeprefix("tzdata/zoneinfo/")] = raw
            if ".dist-info/licenses/" in name and not name.endswith("/"):
                licenses[name.split(".dist-info/licenses/", 1)[1].replace("/", "-")] = source.read(name)
    if len(zones) < 500 or not licenses:
        raise ValueError("Timezone source is incomplete")
    destination.mkdir(parents=True, exist_ok=True)
    archive = destination / "iana-timezones.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as target:
        for name, raw in sorted(zones.items()):
            entry = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = 0o644 << 16
            target.writestr(entry, raw)
    for name, raw in licenses.items():
        (destination / ("tzdata-" + name)).write_bytes(raw)
    metadata = {"source": f"https://pypi.org/project/tzdata/{VERSION}/", "version": VERSION,
        "wheel_sha256": WHEEL_SHA256, "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
        "zone_count": len(zones), "scope": "Unmodified TZif data; no executable package code; original licenses retained."}
    (destination / "timezones-source.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return metadata


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wheel", type=Path)
    parser.add_argument("--destination", type=Path, default=ROOT / "skills/book-genesis/scripts/data")
    args = parser.parse_args()
    print(json.dumps(build(args.wheel, args.destination), indent=2))
