#!/usr/bin/env python3
"""Merge a Chinese subtitle and a Japanese subtitle into one bilingual ASS."""

import argparse
import json
import re
import statistics
import sys
from pathlib import Path

STAMP = re.compile(r"(\d+):(\d{2}):(\d{2})[.,](\d{1,3})")
ASS_TIME = re.compile(r"(\d+):(\d{2}):(\d{2})\.(\d{2})")
OVERRIDE = re.compile(r"\{[^}]*\}")
SRT_INDEX = re.compile(r"^\d+$")

CN_FALLBACK_FONT = "PingFang SC"
DEFAULT_JP_STYLE = """Style: 日文,{font},{size},&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,2,0,2,10,10,{margin},134
"""


def stamp_seconds(value):
    match = STAMP.search(value)
    if not match:
        return None
    hours, minutes, secs, frac = match.groups()
    return int(hours) * 3600 + int(minutes) * 60 + int(secs) + int(frac.ljust(3, "0")) / 1000


def ass_time(seconds):
    seconds = max(0.0, seconds)
    hours, rest = divmod(seconds, 3600)
    minutes, rest = divmod(rest, 60)
    return f"{int(hours)}:{int(minutes):02d}:{rest:05.2f}"


def decode(raw):
    # Chinese fansub releases ship UTF-16LE with a BOM as often as UTF-8;
    # decoding those bytes as gb18030 silently yields mojibake.
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return raw.decode("utf-16")
    for encoding in ("utf-8-sig", "utf-8", "gb18030", "cp932"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", "replace")


def parse_srt(text):
    events = []
    block = []
    for line in text.splitlines() + [""]:
        if line.strip():
            block.append(line)
            continue
        if block:
            index = 0
            if SRT_INDEX.match(block[0].strip()) and len(block) > 1:
                index = 1
            if index < len(block) and "-->" in block[index]:
                left, right = block[index].split("-->", 1)
                start = stamp_seconds(left)
                end = stamp_seconds(right)
                body = "\\N".join(part.strip() for part in block[index + 1:] if part.strip())
                if start is not None and end is not None and body:
                    events.append((start, end, OVERRIDE.sub("", body).strip()))
            block = []
    return events


def parse_ass(text):
    """Keep each original Dialogue line so Chinese styling and positioning survive."""
    events = []
    in_events = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("["):
            in_events = stripped.lower() == "[events]"
            continue
        if not in_events or not stripped.startswith("Dialogue:"):
            continue
        fields = stripped[len("Dialogue:"):].split(",", 9)
        if len(fields) < 10:
            continue
        start = stamp_seconds(fields[1])
        end = stamp_seconds(fields[2])
        if start is None or end is None:
            continue
        events.append({"start": start, "end": end, "raw": stripped, "body": fields[9].strip()})
    return events


def parse_srt_events(text):
    return [{"start": start, "end": end, "body": body} for start, end, body in parse_srt(text)]


def parse(path):
    text = decode(path.read_bytes())
    if path.suffix.lower() in (".ass", ".ssa"):
        return text, parse_ass(text), True
    return text, parse_srt_events(text), False


def style_block(text):
    """Return header lines plus the styles section, without the events section.

    Script Info has to travel with the styles. PlayResX/PlayResY live there, and
    without them libass assumes a 384x288 canvas, which blows a 1080p font up
    until it covers the picture.
    """
    header, styles = [], []
    section = None
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            section = stripped.lower()
            if section == "[events]":
                break
            (styles if "styles" in section else header).append(line)
            continue
        if section is not None and "styles" in section:
            styles.append(line)
        else:
            header.append(line)
    return header, styles


def split_style(line):
    parts = line.split(":", 1)[1].split(",")
    parts[0] = parts[0].strip()
    return parts


def style_number(parts, index, default):
    if index >= len(parts):
        return default
    try:
        return float(parts[index])
    except ValueError:
        return default


def anchor_style(style_lines, events):
    """The Chinese dialogue style the Japanese line has to clear.

    Fansubs often mark the spoken style with a leading asterisk in the dialogue
    (`*Default`) while the style itself is named `Default`. Count both.
    """
    counts = {}
    for event in events:
        raw = event.get("raw", "")
        fields = raw.split(",", 9) if raw else []
        name = fields[3].lstrip("*").strip() if len(fields) > 3 else "中文"
        counts[name] = counts.get(name, 0) + 1
    parsed = []
    for line in style_lines:
        if not line.strip().startswith("Style:"):
            continue
        parts = split_style(line)
        if parts[0] == "日文":
            continue
        parsed.append(parts)
    bottoms = [parts for parts in parsed if int(style_number(parts, 18, 2)) in (1, 2, 3)]
    pool = bottoms or parsed
    if not pool:
        return 48.0, 20.0
    best = max(pool, key=lambda parts: (counts.get(parts[0], 0), style_number(parts, 2, 0)))
    return style_number(best, 2, 48), style_number(best, 21, 10)


def japanese_metrics(size, margin):
    """A slightly smaller Japanese line, sitting fully above the Chinese one."""
    fitted = max(16, round(size * 0.72))
    gap = max(8, round(size * 0.15))
    return fitted, int(margin + size + gap)


def ensure_playres(header, play_x=1920, play_y=1080):
    if any(line.lower().startswith("playresy") for line in header):
        return header
    header = list(header)
    if not any(line.strip() == "[Script Info]" for line in header):
        header = ["[Script Info]", "ScriptType: v4.00+"] + header
    inserted = []
    done = False
    for line in header:
        inserted.append(line)
        if not done and line.strip() == "[Script Info]":
            inserted.append(f"PlayResX: {play_x}")
            inserted.append(f"PlayResY: {play_y}")
            done = True
    return inserted


def repair(text, play_x, play_y, jp_font="EPSON 太明朝体Ｂ"):
    """Put PlayRes back and refit the Japanese style on an already merged script.

    Dialogue timestamps stay untouched; only the canvas and the added style change.
    """
    text = text.lstrip("\ufeff")
    header, styles = style_block(text)
    header = [line for line in header if not line.lower().startswith(("playresx", "playresy"))]
    header = ensure_playres(header, play_x, play_y)
    cleaned, seen = [], False
    for line in styles:
        if line.strip().lower() == "[v4+ styles]":
            if seen:
                continue
            seen = True
        cleaned.append(line)
    size, margin = japanese_metrics(*anchor_style(cleaned, parse_ass(text)))
    refit = DEFAULT_JP_STYLE.format(font=jp_font, size=size, margin=margin).rstrip()
    cleaned = [refit if line.strip().startswith("Style: 日文") else line for line in cleaned]
    if not any(line.strip().startswith("Style: 日文") for line in cleaned):
        cleaned.append(refit)
    dialogue = [line for line in text.splitlines() if line.startswith("Dialogue:")]
    lines = list(header)
    if not seen:
        lines.append("[V4+ Styles]")
    lines.extend(cleaned)
    lines.append("[Events]")
    lines.append("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text")
    lines.extend(dialogue)
    return "\n".join(lines) + "\n"


TYPESET = re.compile(r"\\pos|\\move|\\clip|\\fad|\\t\(|\\k[fo]?\\|\\[a-zA-Z]*c&H")


def plain(event):
    """True for an ordinary spoken line, false for signs, karaoke and effects.

    Typesetting lines are placed by absolute coordinates and split differently in
    every script, so including them in an offset estimate only adds noise.
    """
    if TYPESET.search(event["body"]):
        return False
    return 0.2 <= event["end"] - event["start"] <= 15


def estimate_offset(cn_events, jp_events, window=15.0, tolerance=0.5):
    """Find the dominant constant shift between the two scripts.

    Matching each Japanese line to its nearest Chinese line fails as soon as the
    two scripts split sentences differently: the nearest line is then usually a
    short typeset or karaoke event, and the median collapses to zero. Voting on
    every plausible pair instead surfaces the shift that most pairs agree on.
    """
    cn_starts = [event["start"] for event in cn_events if plain(event)]
    jp_starts = [event["start"] for event in jp_events if plain(event)]
    if not cn_starts or not jp_starts:
        return 0.0, 0.0, 0

    diffs = []
    for jp_start in jp_starts:
        for cn_start in cn_starts:
            diff = cn_start - jp_start
            if abs(diff) <= window:
                diffs.append(diff)
    if not diffs:
        return 0.0, 0.0, 0

    votes = {}
    for diff in diffs:
        key = round(diff * 10)
        votes[key] = votes.get(key, 0) + 1
    peak = max(votes, key=lambda key: votes[key]) / 10

    cluster = [diff for diff in diffs if abs(diff - peak) <= tolerance]
    offset = statistics.median(cluster)
    spread = statistics.median([abs(diff - offset) for diff in cluster])
    return offset, spread, len(cluster)


def build(cn_path, jp_path, out_path, jp_font, jp_size, jp_margin, force_offset=None, dry=False):
    cn_text, cn_events, cn_is_ass = parse(cn_path)
    _, jp_events, jp_is_ass = parse(jp_path)
    offset, spread, matched = estimate_offset(cn_events, jp_events)
    applied = force_offset if force_offset is not None else (offset if spread <= 0.6 else 0.0)

    header, styles = style_block(cn_text)
    header = ensure_playres(header)
    cleaned = [line for line in styles if not line.strip().startswith("Style: 日文")]
    if not any(line.strip().lower().startswith("format:") for line in cleaned):
        cleaned.append("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
                       "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, "
                       "ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, "
                       "MarginR, MarginV, Encoding")
    if not cn_is_ass:
        cleaned.append(f"Style: 中文,{CN_FALLBACK_FONT},60,&H00FFFFFF,&H000000FF,"
                       f"&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,2,0,2,10,10,15,134")
    fitted_size, fitted_margin = japanese_metrics(*anchor_style(cleaned, cn_events))
    cleaned.append(DEFAULT_JP_STYLE.format(
        font=jp_font,
        size=jp_size if jp_size is not None else fitted_size,
        margin=jp_margin if jp_margin is not None else fitted_margin,
    ).rstrip())

    dialogue = []
    for event in cn_events:
        if "raw" in event:
            dialogue.append((event["start"], 0, event["raw"]))
        else:
            start, end = event["start"], event["end"]
            body = event["body"].replace("\n", "\\N")
            dialogue.append((start, 0, f"Dialogue: 0,{ass_time(start)},{ass_time(end)},中文,,0,0,0,,{body}"))
    for event in jp_events:
        start, end = event["start"] + applied, event["end"] + applied
        if start < 0:
            continue
        body = event["body"].replace("\n", "\\N")
        dialogue.append((start, 1, f"Dialogue: 0,{ass_time(start)},{ass_time(end)},日文,,0,0,0,,{body}"))
    dialogue.sort(key=lambda item: (item[0], item[1]))

    if dry:
        return {"cn_events": len(cn_events), "jp_events": len(jp_events),
                "offset": round(applied, 3), "spread": round(spread, 3), "matched": matched}

    lines = list(header)
    if not any(line.strip().lower() == "[v4+ styles]" for line in cleaned):
        lines.append("[V4+ Styles]")
    lines.extend(cleaned)
    lines.append("[Events]")
    lines.append("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text")
    lines.extend(item[2] for item in dialogue)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"cn_events": len(cn_events), "jp_events": len(jp_events),
            "offset": round(applied, 3), "spread": round(spread, 3), "matched": matched}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cn", required=True, type=Path, help="Chinese ASS/SSA/SRT")
    parser.add_argument("--jp", required=True, type=Path, help="Japanese ASS/SSA/SRT")
    parser.add_argument("--out", type=Path, help="merged ASS to write")
    parser.add_argument("--jp-font", default="EPSON 太明朝体Ｂ")
    parser.add_argument("--jp-size", type=int, default=None,
                        help="Japanese font size in PlayRes pixels; default follows the Chinese style")
    parser.add_argument("--jp-margin", type=int, default=None,
                        help="vertical margin of the Japanese line; default clears the Chinese line")
    parser.add_argument("--offset", type=float, default=None,
                        help="force a shift in seconds instead of using detection")
    parser.add_argument("--dry-run", action="store_true", help="report without writing")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    if not args.out and not args.dry_run:
        parser.error("--out is required unless --dry-run is used")

    stats = build(args.cn, args.jp, args.out, args.jp_font, args.jp_size,
                  args.jp_margin, args.offset, args.dry_run)
    if args.json:
        json.dump(stats, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        print(f"cn={stats['cn_events']} jp={stats['jp_events']} "
              f"offset={stats['offset']:+.2f}s spread={stats['spread']:.2f}s "
              f"matched={stats['matched']}")
        if stats["spread"] > 0.6:
            print("warning: timing unreliable, pass --offset explicitly", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())