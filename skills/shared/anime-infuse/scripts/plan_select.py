"""Report which files of a torrent are already on disk and which still need downloading.

Used to stitch a series together from several releases: keep the files one torrent
already delivered, then ask aria2 for only the gaps.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from torrent_files import human, parse_torrent  # noqa: E402


def status_of(path: Path, expected: int) -> tuple[str, int]:
    """Classify one file and return (state, bytes already present)."""
    if not path.exists():
        return "missing", 0
    actual = path.stat().st_size
    if actual >= expected:
        return "complete", expected
    return "partial", actual


def compress(indices):
    """Render 1,2,3,7,9,10 as 1-3,7,9-10 so aria2c --select-file stays readable."""
    runs = []
    for index in indices:
        if runs and index == runs[-1][-1] + 1:
            runs[-1].append(index)
        else:
            runs.append([index])
    return ",".join(str(run[0]) if len(run) == 1 else f"{run[0]}-{run[-1]}" for run in runs)


def survey(torrent: Path, directory: Path):
    """Return the per-file state for every file in the torrent."""
    name, files = parse_torrent(torrent.read_bytes())
    rooted = directory / name
    rows = []
    for entry in files:
        # aria2 writes multi-file torrents under a folder named after the torrent,
        # but a directory pointed straight at that folder is just as valid.
        candidates = [rooted / entry["path"], directory / entry["path"]]
        state, present = "missing", 0
        for candidate in candidates:
            found, size = status_of(candidate, entry["size"])
            if found != "missing":
                state, present = found, size
                break
        rows.append({**entry, "state": state, "present": present})
    return rows


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("torrent", type=Path)
    parser.add_argument("--dir", type=Path, default=Path("."),
                        help="directory already holding (some) files")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    rows = survey(args.torrent, args.dir)
    todo = [row["index"] for row in rows if row["state"] != "complete"]

    if args.json:
        json.dump({
            "directory": str(args.dir),
            "files": rows,
            "select": todo,
            "select_arg": compress(todo),
        }, sys.stdout, indent=2)
        return 0 if todo else 1

    for state in ("complete", "partial", "missing"):
        chosen = [row for row in rows if row["state"] == state]
        size = sum(row["present"] if state == "partial" else row["size"] for row in chosen)
        print(f"{state:<9} {len(chosen):>3} files  {human(size)}")
        if state != "complete":
            for row in chosen:
                got = f"{human(row['present'])}/" if state == "partial" else ""
                print(f"  [{row['index']:>3}] {got}{human(row['size'])}  {row['path']}")

    if not todo:
        print("\nnothing to download")
        return 1
    print(f"\nsuggested: --select-file={compress(todo)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())