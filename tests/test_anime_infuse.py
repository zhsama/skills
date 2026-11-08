import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHECK = ROOT / "skills/anime-infuse/scripts/check_subs.py"
TORRENT = ROOT / "skills/anime-infuse/scripts/torrent_files.py"

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


if __name__ == "__main__":
    unittest.main()