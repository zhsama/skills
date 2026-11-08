#!/usr/bin/env python3
"""Report subtitle tracks in a media file or a subtitle file, and detect Chinese/Japanese pairing."""

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

KANA = re.compile(r"[\u3040-\u30ff\uff66-\uff9f]")
HAN = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")
OVERRIDE = re.compile(r"\{[^}]*\}")
STAMP = re.compile(r"(\d+):(\d{2}):(\d{2})[.,](\d{1,3})")
TEXT_SUFFIXES = (".ass", ".ssa", ".srt", ".vtt")
TEXT_CODECS = ("ass", "ssa", "subrip", "webvtt", "mov_text")


def stamp_seconds(value):
    match = STAMP.search(value)
    if not match:
        return None
    hours, minutes, secs, frac = match.groups()
    return int(hours) * 3600 + int(minutes) * 60 + int(secs) + int(frac.ljust(3, "0")) / 1000


def decode(raw):
    for encoding in ("utf-8-sig", "utf-8", "gb18030", "cp932"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", "replace")


def classify(text):
    if KANA.search(text):
        return "jp"
    if HAN.search(text):
        return "zh"
    return "neutral"


def strip_marks(text):
    return OVERRIDE.sub("", text).replace("\\N", " ").replace("\\n", " ").strip()


def add_line(styles, style, body):
    cleaned = strip_marks(body)
    if not cleaned:
        return
    bucket = styles.setdefault(style, {"lines": 0, "jp": 0, "zh": 0, "neutral": 0})
    bucket["lines"] += 1
    bucket[classify(cleaned)] += 1


def analyze_text(text):
    """Count lines per style, classify each style's language, and return the last event time."""
    styles = {}
    last_end = 0.0
    lines = text.splitlines()

    if any(marker in text for marker in ("[V4+ Styles]", "[V4 Styles]", "[Events]")):
        in_events = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("["):
                in_events = stripped.lower() == "[events]"
                continue
            if not in_events or not stripped.startswith("Dialogue:"):
                continue
            fields = stripped[len("Dialogue:"):].split(",", 9)
            if len(fields) < 10:
                continue
            end = stamp_seconds(fields[2])
            if end:
                last_end = max(last_end, end)
            add_line(styles, fields[3].strip(), fields[9])
    else:
        style = "default"
        collecting = False
        for line in lines:
            stripped = line.strip()
            if "-->" in stripped:
                right = stripped.split("-->", 1)[1]
                end = stamp_seconds(right)
                if end:
                    last_end = max(last_end, end)
                tail = OVERRIDE.sub("", right.split("}", 1)[-1])
                tail = re.sub(r"^\s*\d+:\d{2}:\d{2}[.,]\d{1,3}", "", tail).strip()
                if tail:
                    add_line(styles, style, tail)
                collecting = True
                continue
            if not stripped:
                collecting = False
                continue
            if collecting and not stripped.isdigit():
                add_line(styles, style, stripped)

    for bucket in styles.values():
        if bucket["jp"] > bucket["zh"] * 3 and bucket["jp"]:
            bucket["language"] = "ja"
        elif bucket["zh"] > bucket["jp"] * 3 and bucket["zh"]:
            bucket["language"] = "zh"
        elif bucket["jp"] and bucket["zh"]:
            bucket["language"] = "mixed"
        else:
            bucket["language"] = "other"
    return styles, last_end


def bilingual_verdict(styles):
    """Compare the best-matching Japanese/Chinese style pair.

    Sign and staff styles are often monolingual, so comparing language totals
    misjudges a correctly paired script. Pair styles instead and judge the
    closest match.
    """
    japanese = [(name, s) for name, s in styles.items() if s["language"] == "ja"]
    chinese = [(name, s) for name, s in styles.items() if s["language"] == "zh"]
    if not japanese or not chinese:
        jp_lines = sum(s["lines"] for _, s in japanese)
        zh_lines = sum(s["lines"] for _, s in chinese)
        return False, jp_lines, zh_lines, "only one language detected"

    candidates = []
    for jp_name, jp in japanese:
        for zh_name, zh in chinese:
            largest = max(jp["lines"], zh["lines"]) or 1
            gap = abs(jp["lines"] - zh["lines"]) / largest
            candidates.append((gap, -min(jp["lines"], zh["lines"]),
                              jp_name, jp["lines"], zh_name, zh["lines"]))
    candidates.sort()
    gap, _, jp_name, jp_lines, zh_name, zh_lines = candidates[0]
    paired = gap <= 0.15
    detail = (f"paired {jp_name} / {zh_name}" if paired
              else f"closest pair differs by {gap:.0%}")
    return paired, jp_lines, zh_lines, detail


def probe(path):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-print_format", "json",
         "-show_streams", "-show_format", str(path)],
        capture_output=True, text=True)
    if result.returncode != 0:
        raise SystemExit(f"ffprobe failed: {result.stderr.strip()}")
    return json.loads(result.stdout)


def extract(path, subtitle_index, target):
    result = subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-i", str(path),
         "-map", f"0:s:{subtitle_index}", "-f", "ass", str(target)],
        capture_output=True, text=True)
    return result.returncode == 0


def extract_all(path, target_dir, as_json=False):
    """Write every text subtitle track of a media file out as an .ass file."""
    data = probe(path)
    subtitles = [s for s in data["streams"] if s["codec_type"] == "subtitle"]
    target_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for position, stream in enumerate(subtitles):
        if stream["codec_name"] not in TEXT_CODECS:
            continue
        language = stream.get("tags", {}).get("language", "und")
        target = target_dir / f"{path.stem}.s{position}.{language}.ass"
        if extract(path, position, target):
            written.append(str(target))
    if as_json:
        json.dump({"file": path.name, "extracted": written}, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        for name in written:
            print(name)
        if not written:
            print(f"{path.name}: no text subtitle track to extract")
    return 0 if written else 1


def describe(styles, verdict, jp_lines, zh_lines, detail, as_json):
    if as_json:
        return {"styles": styles, "bilingual": verdict,
                "jp_lines": jp_lines, "zh_lines": zh_lines, "detail": detail}
    for style, bucket in sorted(styles.items(), key=lambda kv: -kv[1]["lines"]):
        print(f"        {style[:26]:<26} {bucket['lines']:>4} lines  "
              f"jp={bucket['jp']:<4} zh={bucket['zh']:<4} {bucket['language']}")
    label = "BILINGUAL" if verdict else "not bilingual"
    print(f"        -> {label} (jp={jp_lines} zh={zh_lines}) {detail}")
    return None


def report_media(path, as_json):
    data = probe(path)
    duration = float(data["format"].get("duration") or 0)
    subtitles = [s for s in data["streams"] if s["codec_type"] == "subtitle"]
    attachments = [s for s in data["streams"] if s["codec_type"] == "attachment"]

    rows = []
    with tempfile.TemporaryDirectory() as directory:
        for position, stream in enumerate(subtitles):
            tags = stream.get("tags", {})
            disposition = stream.get("disposition", {})
            row = {
                "index": position,
                "codec": stream["codec_name"],
                "language": tags.get("language", "und"),
                "title": tags.get("title", ""),
                "default": bool(disposition.get("default")),
                "forced": bool(disposition.get("forced")),
                "bilingual": False,
                "last_event": 0.0,
            }
            if stream["codec_name"] in TEXT_CODECS:
                target = Path(directory) / f"s{position}.ass"
                if extract(path, position, target):
                    styles, last_end = analyze_text(decode(target.read_bytes()))
                    verdict, jp_lines, zh_lines, detail = bilingual_verdict(styles)
                    row.update(styles=styles, bilingual=verdict, jp_lines=jp_lines,
                               zh_lines=zh_lines, detail=detail,
                               last_event=round(last_end, 2))
            rows.append(row)

    if as_json:
        json.dump({"file": path.name, "duration": duration, "subtitles": rows,
                   "attachments": len(attachments)}, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0

    print(f"{path.name}  duration {duration:.1f}s  "
          f"{len(subtitles)} subtitle track(s)  {len(attachments)} font attachment(s)")
    for row in rows:
        flags = " ".join(name for name in ("default", "forced") if row[name])
        label = f"{row['language']}/{row['title']}" if row["title"] else row["language"]
        print(f"  [s:{row['index']}] {row['codec']:<8} {label:<26} {flags}")
        if row.get("styles"):
            describe(row["styles"], row["bilingual"], row["jp_lines"],
                     row["zh_lines"], row["detail"], False)
            if duration and row["last_event"] > duration + 1:
                print(f"        -> WARNING last event {row['last_event']}s "
                      f"exceeds duration {duration:.1f}s")
    return 0


def report_text(path, as_json):
    styles, last_end = analyze_text(decode(path.read_bytes()))
    verdict, jp_lines, zh_lines, detail = bilingual_verdict(styles)
    if as_json:
        json.dump({"file": path.name, "styles": styles, "bilingual": verdict,
                   "jp_lines": jp_lines, "zh_lines": zh_lines,
                   "last_event": round(last_end, 2)}, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0
    print(f"{path.name}  last event {last_end:.1f}s")
    describe(styles, verdict, jp_lines, zh_lines, detail, False)
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", help="media file or subtitle file")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    parser.add_argument("--extract", type=Path, metavar="DIR",
                        help="write every text subtitle track of a media file into DIR")
    args = parser.parse_args(argv)

    path = Path(args.path).expanduser()
    if not path.is_file():
        parser.error(f"no such file: {path}")
    if args.extract:
        return extract_all(path, args.extract.expanduser(), args.json)
    if path.suffix.lower() in TEXT_SUFFIXES:
        return report_text(path, args.json)
    return report_media(path, args.json)


if __name__ == "__main__":
    sys.exit(main())