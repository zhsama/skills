#!/usr/bin/env python3
"""List the files inside a .torrent with the index aria2c needs for --select-file."""

import argparse
import json
import sys
from pathlib import Path

ARCHIVE_SUFFIXES = (".zip", ".7z", ".rar", ".tar", ".gz")
SUBTITLE_SUFFIXES = (".ass", ".ssa", ".srt", ".sup", ".vtt")


def bdecode(data, index=0):
    marker = data[index:index + 1]
    if marker == b"i":
        end = data.index(b"e", index)
        return int(data[index + 1:end]), end + 1
    if marker == b"l":
        index += 1
        items = []
        while data[index:index + 1] != b"e":
            value, index = bdecode(data, index)
            items.append(value)
        return items, index + 1
    if marker == b"d":
        index += 1
        result = {}
        while data[index:index + 1] != b"e":
            key, index = bdecode(data, index)
            value, index = bdecode(data, index)
            result[key] = value
        return result, index + 1
    if marker.isdigit():
        colon = data.index(b":", index)
        length = int(data[index:colon])
        start = colon + 1
        return data[start:start + length], start + length
    raise ValueError(f"unexpected token at byte {index}: {marker!r}")


def parse_torrent(raw):
    """Return (name, files) where files is a list of dicts with a 1-based index."""
    meta, _ = bdecode(raw)
    info = meta[b"info"]
    name = info.get(b"name", b"").decode("utf-8", "replace")
    entries = info.get(b"files")
    if entries is None:
        return name, [{
            "index": 1,
            "size": info.get(b"length", 0),
            "path": name,
        }]
    files = []
    for position, entry in enumerate(entries, start=1):
        parts = [part.decode("utf-8", "replace") for part in entry[b"path"]]
        files.append({
            "index": position,
            "size": entry[b"length"],
            "path": "/".join(parts),
        })
    return name, files


def human(size):
    value = float(size)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if value < 1024 or unit == "TiB":
            return f"{value:.0f} {unit}" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024
    return f"{size} B"


def kind(path):
    lowered = path.lower()
    if lowered.endswith(ARCHIVE_SUFFIXES):
        return "archive"
    if lowered.endswith(SUBTITLE_SUFFIXES):
        return "subtitle"
    return "video"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("torrent", help="path to a .torrent file")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    parser.add_argument("--only", choices=["archive", "subtitle", "video"],
                        help="restrict output to one kind")
    args = parser.parse_args(argv)

    path = Path(args.torrent).expanduser()
    if not path.is_file():
        parser.error(f"no such torrent: {path}")

    name, files = parse_torrent(path.read_bytes())
    if args.only:
        files = [entry for entry in files if kind(entry["path"]) == args.only]

    if args.json:
        json.dump({"name": name, "files": files}, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0

    print(f"{name}  ({len(files)} files, {human(sum(f['size'] for f in files))})")
    for entry in files:
        print(f"  [{entry['index']:>3}] {human(entry['size']):>9}  "
              f"{kind(entry['path']):<8} {entry['path']}")

    wanted = [entry for entry in files if kind(entry["path"]) in ("archive", "subtitle")]
    if wanted:
        selection = ",".join(str(entry["index"]) for entry in wanted)
        print(f"\nTo fetch only subtitles and fonts:\n  --select-file={selection}")
    return 0


if __name__ == "__main__":
    sys.exit(main())