import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHECK = ROOT / "skills/anime-infuse/scripts/check_subs.py"
TORRENT = ROOT / "skills/anime-infuse/scripts/torrent_files.py"
MERGE = ROOT / "skills/anime-infuse/scripts/merge_bilingual.py"
PLAN = ROOT / "skills/anime-infuse/scripts/plan_select.py"

ASS_BILINGUAL = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: TEXT-JP,JP Font,39,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2.7,0,2,0,0,15,128
Style: TEXT-CN,CN Font,60,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2.7,0,2,0,0,15,134
Style: STAFF,CN Font,42,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,1,15,15,15,134

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:01.00,0:00:02.00,TEXT-JP,,0,0,0,,これはテストです
Dialogue: 0,0:00:01.00,0:00:02.00,TEXT-CN,,0,0,0,,这是测试
Dialogue: 0,0:00:03.00,0:00:04.00,TEXT-JP,,0,0,0,,もう一度
Dialogue: 0,0:00:03.00,0:00:04.00,TEXT-CN,,0,0,0,,再来一次
Dialogue: 0,0:00:05.00,0:00:06.00,TEXT-JP,,0,0,0,,終わり
Dialogue: 0,0:00:05.00,0:00:06.00,TEXT-CN,,0,0,0,,结束了
Dialogue: 0,0:00:07.00,0:00:08.00,STAFF,,0,0,0,,制作人员名单
"""

SRT_CHINESE_ONLY = """1
00:00:01,000 --> 00:00:02,000
这是中文

2
00:00:03,000 --> 00:00:04,000
还是中文
"""


def bencode(value):
    if isinstance(value, int):
        return b"i%de" % value
    if isinstance(value, bytes):
        return b"%d:%s" % (len(value), value)
    if isinstance(value, str):
        return bencode(value.encode())
    if isinstance(value, list):
        return b"l" + b"".join(bencode(item) for item in value) + b"e"
    if isinstance(value, dict):
        body = b"".join(bencode(key) + bencode(value[key]) for key in sorted(value))
        return b"d" + body + b"e"
    raise TypeError(type(value))


def make_torrent(directory):
    info = {
        "name": "Example Show",
        "files": [
            {"length": 1024, "path": ["Season 1", "Example - S01E01.mkv"]},
            {"length": 2048, "path": ["Season 1", "Example - S01E02.mkv"]},
            {"length": 512, "path": ["Sub.zip"]},
        ],
    }
    path = Path(directory) / "example.torrent"
    path.write_bytes(bencode({"announce": "udp://example.invalid:6969", "info": info}))
    return path


class SubtitleDetection(unittest.TestCase):
    def run_check(self, path, *extra):
        result = subprocess.run([sys.executable, str(CHECK), str(path), *extra],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def test_pairs_styles_despite_monolingual_signs(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "episode.ass"
            path.write_text(ASS_BILINGUAL)
            output = self.run_check(path, "--json")
            data = json.loads(output)
            self.assertTrue(data["bilingual"])
            self.assertEqual(data["jp_lines"], 3)
            self.assertEqual(data["zh_lines"], 3)
            self.assertEqual(data["last_event"], 8.0)

    def test_single_language_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "episode.srt"
            path.write_text(SRT_CHINESE_ONLY)
            data = json.loads(self.run_check(path, "--json"))
            self.assertFalse(data["bilingual"])
            self.assertEqual(data["zh_lines"], 2)
            self.assertEqual(data["jp_lines"], 0)


class TorrentListing(unittest.TestCase):
    def test_reports_indices_and_select_file_hint(self):
        with tempfile.TemporaryDirectory() as directory:
            torrent = make_torrent(directory)
            result = subprocess.run([sys.executable, str(TORRENT), str(torrent)],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertRegex(result.stdout, r"\[  3\]\s+512 B\s+archive")
            self.assertIn("archive", result.stdout)
            self.assertIn("--select-file=3", result.stdout)

    def test_json_matches_file_order(self):
        with tempfile.TemporaryDirectory() as directory:
            torrent = make_torrent(directory)
            result = subprocess.run([sys.executable, str(TORRENT), str(torrent), "--json"],
                                    capture_output=True, text=True)
            data = json.loads(result.stdout)
            self.assertEqual(data["name"], "Example Show")
            self.assertEqual([item["index"] for item in data["files"]], [1, 2, 3])
            self.assertEqual(data["files"][2]["path"], "Sub.zip")


CN_ASS = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: 简体,方正准圆_GBK,60,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,2,0,2,10,10,15,134

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:02.00,0:00:04.50,简体,,0,0,0,,第一句
Dialogue: 0,0:00:06.00,0:00:08.00,简体,,0,0,0,,第二句
"""

JP_SRT = """1
00:00:02,200 --> 00:00:04,700
最初の台詞

2
00:00:06,200 --> 00:00:08,200
二番目の台詞
"""


class BilingualMerge(unittest.TestCase):
    def merge(self, directory, *extra):
        cn = Path(directory) / "cn.ass"
        jp = Path(directory) / "jp.srt"
        out = Path(directory) / "out.ass"
        cn.write_text(CN_ASS)
        jp.write_text(JP_SRT)
        result = subprocess.run([sys.executable, str(MERGE), "--cn", str(cn),
                                 "--jp", str(jp), "--out", str(out), *extra],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return out, result.stdout

    def test_detects_offset_and_keeps_chinese_style(self):
        with tempfile.TemporaryDirectory() as directory:
            out, output = self.merge(directory, "--json")
            stats = json.loads(output)
            self.assertAlmostEqual(stats["offset"], -0.2, places=2)
            self.assertEqual(stats["cn_events"], 2)
            self.assertEqual(stats["jp_events"], 2)
            merged = out.read_text()
            self.assertIn("Style: 简体,方正准圆_GBK", merged)
            self.assertIn("PlayResX: 1920", merged)
            self.assertIn("PlayResY: 1080", merged)
            self.assertEqual(merged.count("[V4+ Styles]"), 1)
            self.assertIn("Dialogue: 0,0:00:02.00,0:00:04.50,简体", merged)
            self.assertIn("日文,,0,0,0,,最初の台詞", merged)
            self.assertEqual(merged.count("Dialogue:"), 4)
            # Chinese is 60px at margin 15; Japanese must be smaller and clear it.
            jp = next(line for line in merged.splitlines() if line.startswith("Style: 日文"))
            fields = jp.split(",")
            self.assertLess(int(fields[2]), 60)
            self.assertGreaterEqual(int(fields[-2]), 15 + 60)

    def test_repair_puts_playres_back(self):
        broken = """[Script Info]
[V4+ Styles]
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,FZ,65,&H00FFFFFF,&H00000000,&H00000000,&H32000000,-1,0,0,0,100,100,1,0,1,2,0,2,30,30,30,1
Style: 日文,EPSON,42,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,2,0,2,10,10,58,134
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:03:12.40,0:03:14.00,*Default,NTP,0000,0000,0000,,饭做好了
"""
        spec = importlib.util.spec_from_file_location("merge_bilingual", MERGE)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        fixed = module.repair(broken, 1920, 1080)
        self.assertIn("PlayResY: 1080", fixed)
        self.assertEqual(fixed.count("[V4+ Styles]"), 1)
        self.assertIn("饭做好了", fixed)
        jp = next(line for line in fixed.splitlines() if line.startswith("Style: 日文"))
        self.assertGreaterEqual(int(jp.split(",")[-2]), 30 + 65)

    def test_output_reads_as_bilingual(self):
        with tempfile.TemporaryDirectory() as directory:
            out, _ = self.merge(directory)
            result = subprocess.run([sys.executable, str(CHECK), str(out), "--json"],
                                    capture_output=True, text=True)
            self.assertTrue(json.loads(result.stdout)["bilingual"])

    def test_dry_run_writes_nothing(self):
        with tempfile.TemporaryDirectory() as directory:
            cn = Path(directory) / "cn.ass"
            jp = Path(directory) / "jp.srt"
            cn.write_text(CN_ASS)
            jp.write_text(JP_SRT)
            result = subprocess.run([sys.executable, str(MERGE), "--cn", str(cn),
                                     "--jp", str(jp), "--dry-run", "--json"],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["jp_events"], 2)

    def test_reads_utf16_chinese_script(self):
        with tempfile.TemporaryDirectory() as directory:
            cn = Path(directory) / "cn.ass"
            jp = Path(directory) / "jp.srt"
            cn.write_bytes(CN_ASS.encode("utf-16"))
            jp.write_text(JP_SRT)
            result = subprocess.run([sys.executable, str(MERGE), "--cn", str(cn),
                                     "--jp", str(jp), "--dry-run", "--json"],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            stats = json.loads(result.stdout)
            self.assertEqual(stats["cn_events"], 2)
            self.assertAlmostEqual(stats["offset"], -0.2, places=2)

    def test_offset_survives_typesetting_and_split_lines(self):
        """Dense signs and a script that splits lines differently must not hide the shift."""
        chinese = CN_ASS.replace(
            "Dialogue: 0,0:00:02.00,0:00:04.50,简体,,0,0,0,,第一句\n"
            "Dialogue: 0,0:00:06.00,0:00:08.00,简体,,0,0,0,,第二句\n",
            "".join(
                f"Dialogue: 0,0:00:{10 + 2 * step:02d}.00,0:00:{12 + 2 * step:02d}.00,"
                f"简体,,0,0,0,,台词{step}\n"
                for step in range(10)
            )
            + "Dialogue: 0,0:00:40.00,0:00:42.00,简体,,0,0,0,,{\\pos(50,50)\\fad(100,100)}招牌\n",
        )
        japanese = "".join(
            f"{step + 1}\n00:00:{17 + 2 * step:02d},500 --> 00:00:{19 + 2 * step:02d},000\n台詞{step}\n\n"
            for step in range(5)
        )
        with tempfile.TemporaryDirectory() as directory:
            cn = Path(directory) / "cn.ass"
            jp = Path(directory) / "jp.srt"
            cn.write_text(chinese)
            jp.write_text(japanese)
            result = subprocess.run([sys.executable, str(MERGE), "--cn", str(cn),
                                     "--jp", str(jp), "--dry-run", "--json"],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            stats = json.loads(result.stdout)
            # 中文台词在 10,12,14…秒；日文台词在 17.5,19.5,21.5…秒，即晚 7.5s
            self.assertAlmostEqual(stats["offset"], -7.5, delta=0.6)
            self.assertLess(stats["spread"], 0.2)


class PartialReuse(unittest.TestCase):
    def test_reports_complete_partial_and_missing(self):
        with tempfile.TemporaryDirectory() as directory:
            torrent = make_torrent(directory)
            release = Path(directory) / "Example Show" / "Season 1"
            release.mkdir(parents=True)
            (release / "Example - S01E01.mkv").write_bytes(b"x" * 1024)
            (release / "Example - S01E02.mkv").write_bytes(b"x" * 700)
            result = subprocess.run([sys.executable, str(PLAN), str(torrent),
                                     "--dir", directory], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertRegex(result.stdout, r"complete\s+1 files")
            self.assertRegex(result.stdout, r"partial\s+1 files")
            self.assertRegex(result.stdout, r"missing\s+1 files")
            self.assertIn("--select-file=2-3", result.stdout)

    def test_collapses_consecutive_indices(self):
        with tempfile.TemporaryDirectory() as directory:
            torrent = make_torrent(directory)
            Path(directory, "Example Show", "Season 1").mkdir(parents=True)
            (Path(directory) / "Example Show" / "Sub.zip").write_bytes(b"x" * 512)
            result = subprocess.run([sys.executable, str(PLAN), str(torrent),
                                     "--dir", directory, "--json"],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["select_arg"], "1-2")

    def test_everything_present_reports_nothing_to_do(self):
        with tempfile.TemporaryDirectory() as directory:
            torrent = make_torrent(directory)
            release = Path(directory) / "Example Show"
            (release / "Season 1").mkdir(parents=True)
            (release / "Season 1" / "Example - S01E01.mkv").write_bytes(b"x" * 1024)
            (release / "Season 1" / "Example - S01E02.mkv").write_bytes(b"x" * 2048)
            (release / "Sub.zip").write_bytes(b"x" * 512)
            result = subprocess.run([sys.executable, str(PLAN), str(torrent),
                                     "--dir", directory], capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertIn("nothing to download", result.stdout)


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                     "needs ffmpeg and ffprobe")
class TrackExtraction(unittest.TestCase):
    def make_media(self, directory):
        subtitle = Path(directory) / "in.ass"
        subtitle.write_text(ASS_BILINGUAL)
        media = Path(directory) / "episode.mkv"
        subprocess.run(["ffmpeg", "-v", "error", "-y",
                        "-f", "lavfi", "-i", "color=c=black:s=64x64:d=1",
                        "-i", str(subtitle), "-map", "0:v", "-map", "1:0",
                        "-c:v", "libx264", "-preset", "ultrafast",
                        "-c:s", "ass", "-metadata:s:s:0", "language=chi",
                        str(media)], check=True, capture_output=True)
        return media

    def test_extracts_embedded_text_track(self):
        with tempfile.TemporaryDirectory() as directory:
            media = self.make_media(directory)
            out = Path(directory) / "subs"
            result = subprocess.run([sys.executable, str(CHECK), str(media),
                                     "--extract", str(out)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            written = list(out.glob("*.ass"))
            self.assertEqual(len(written), 1)
            self.assertIn("这是测试", written[0].read_text())


if __name__ == "__main__":
    unittest.main()