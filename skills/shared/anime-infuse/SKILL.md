---
name: anime-infuse
description: "Acquire anime films and series with bilingual Chinese/Japanese subtitles and file them into an Infuse library. Use when the user asks to download anime, wants 中日双语 or 简日双语 subtitles, asks for a season batch from Mikan or Nyaa, needs subtitles rescued from a torrent with no seeders, or wants finished media imported and readable in Infuse."
compatibility: "macOS with aria2c, mkvmerge, ffprobe, and python3. Sites used for searching and subtitles are external and can change or rate-limit."
---

# Anime Infuse

Turn "I want this show with Chinese-Japanese subtitles on my Apple devices" into playable files. Four stages, each with a verification step, because most failures here are silent: a torrent that looks alive, subtitles that turn out to be monolingual, or files that Infuse cannot match.

## Personal defaults

If the `personal-context` skill is installed, read its `references/anime-infuse.md` for the library location and response preferences. Resolve that skill from the skill catalog or as a sibling directory under the same installed skill root. These defaults are optional; an explicit user request takes precedence.

## Stage 1 — Find a release

Search order:

| Source | How | Notes |
| --- | --- | --- |
| Mikan | `https://mikanani.me/RSS/Search?searchstr=<query>` or the HTML search page | Best for 字幕组 batches with bilingual subs |
| Nyaa | `https://nyaa.si/?q=<query>&c=1_2&s=seeders&o=desc` | Reliable seeders, usually English-subbed |
| dmhy | `https://share.dmhy.org/topics/list?keyword=<query>` | Mirrors most Mikan 字幕组 releases |

Do not use the bangumi.moe search API; it returns `{"errno":500}` on every query.

Rank candidates by seeder count first, then by whether the release name advertises bilingual subtitles (`中日双语`, `简日双语`, `简繁日`). A `合辑`/`Batch` is preferable to per-episode files.

Never judge a torrent by the listing. Check the swarm before downloading: fetch the `.torrent`, parse it, and confirm a seeder exists. Releases that advertise the exact subtitles you want are frequently dead, while a well-seeded English-subbed release is not.

## Stage 2 — Get bilingual subtitles

Work through these in order. Stop at the first that yields a track containing both Chinese and Japanese.

1. **Embedded in the release.** Run `python3 scripts/check_subs.py <file.mkv>`. A `chi` ASS track named `简日双语`/`繁日双语`/`中日双语` is the ideal outcome — nothing to source, nothing to mux.
2. **A subtitle archive inside the torrent.** 字幕组 batches ship `Sub.zip` or `SUBS.7z` with separate `.chs.ass` / `.cht.ass` / `.jpn.ass` files, and often the `.chs.ass` is itself bilingual (dual `TEXT-CN` and `TEXT-JP` styles). Download only that file — see Stage 3, selective download. This works even when the torrent has no viable seeder for the video.
3. **External subtitle sites.** kitsunekko has Japanese subtitles per show (paths use the Japanese romanization, e.g. `Zankyou_No_Teroru`, not the English title). assrt.net requires login (HTTP 402 anonymously). subhd and zimuku have thin anime coverage and often return zero results. OpenSubtitles answers automated requests with a bot check.

Verify before trusting any file: `python3 scripts/check_subs.py <file.ass>` and confirm the Chinese and Japanese line counts match. Equal counts across the whole episode indicate a true bilingual script with matching timings.

### When no bilingual release exists

Popular classics often ship as Chinese-only `ASSx2` (one `.sc` and one `.tc` track) while the Japanese script sits on kitsunekko. Build the bilingual track yourself instead of settling for one language.

1. Prefer a release that ships **external** subtitles (`.sc.ass` / `.tc.ass` beside the video, typical of VCB-Studio, Airota&Nekomoe, DBD-Raws). Download only the subtitle files with `--select-file` from `torrent_files.py` — even a nearly dead swarm delivers a few hundred KB.
2. Take the video from a well-seeded English-subbed release on Nyaa. Both are Blu-ray encodes, so timings agree; verify per episode rather than assuming.
3. `python3 scripts/merge_bilingual.py --cn <sc.ass> --jp <jp.srt> --out <merged.ass>` keeps every Chinese style and dialogue line untouched, and keeps the `[Script Info]` block with it. `PlayResX` / `PlayResY` have to survive: libass assumes 384×288 when they are missing, and a font size written for 1080p then covers the frame. A spoken pair is written as one event, Chinese first and Japanese after `\N`, switching to the `日文` style with `{\r日文}`. A second event at the same time gets stacked above the first by players that ignore margins, which puts the original on top of the translation. `\pos` and `\an` signs stay separate events. The report gives the detected offset and its spread. Run it with `--dry-run --json` first; the estimate votes on every plausible line pair and ignores typesetting and karaoke lines, so a low `spread` below 0.2s against a handful of votes means the two scripts genuinely share a timeline. `spread` above 0.6s, or an offset that changes from episode to episode, means they do not — fix the source rather than forcing `--offset`.
4. Check the result with `check_subs.py` (it should now say `BILINGUAL`) and mux it as the only subtitle track.

### Verify the timeline against the video, not against the other script

A subtitle file can be complete, correctly encoded and still unusable: sets are re-timed per release, and kitsunekko often holds several for one show (`Cowboy_Bebop_(01-26)` and `Cowboy_Bebop_(01-26)_(Webrip)`). The older rip set is sometimes authored for an edit with the opening placed first, so its drift grows past a minute mid-episode — no single `--offset` repairs that.

The video's own subtitle track is the only ground truth:

```sh
python3 scripts/check_subs.py episode.mkv --extract /tmp/embed
python3 scripts/merge_bilingual.py --cn /tmp/embed/eng.ass --jp jp.srt --dry-run --json
```

The second command reports the offset between the embedded script and the Japanese one. Trust it over an estimate made from the Chinese script:

- A good set gives the **same** offset (±1s) for every episode, with `spread` under 0.2s. Apply it per episode (`--offset` is only needed when `spread` is high).
- A set timed to another edit gives **different** offsets per episode, or offsets in the tens of seconds. Throw it away and look for the other variant.

Cost of the check is one episode per release — the torrent's own subtitle track comes out of the file you already downloaded.

Chinese scripts are usually authored against the release you took the video from, so check them the same way once: an embedded English track and the Chinese script should land within half a second of each other.

Sanity-check the text too: a Chinese file whose `[Script Info]` says `UTF-16` and whose line count is zero in `merge_bilingual.py` decoded as gb18030 mojibake. UTF-16 BOMs are handled now, but a zero event count on a non-empty file means the decode went wrong.

## Stage 3 — Download in parallel, multi-threaded

Run one aria2 job per release, concurrently, so a stalled source does not block the others:

```sh
aria2c release.torrent --dir="$OUT" \
  --enable-dht=true --dht-listen-port=6881-6999 --bt-max-peers=300 \
  --max-connection-per-server=16 --split=16 --min-split-size=1M \
  --bt-enable-lpd=true --enable-peer-exchange=true \
  --seed-time=0 --file-allocation=none --summary-interval=30
```

Append `--bt-tracker=<comma-separated list>` with public trackers when the torrent's own tracker is dead. Poll the progress line to report per-release speed, and tell the user which source is actually fastest — peak throughput and total wall time are different questions when the releases differ in size by an order of magnitude.

**Selective download** is the technique that rescues subtitles from otherwise-dead torrents. List the files and their indices:

```sh
python3 scripts/torrent_files.py release.torrent
```

Then download just the subtitle archive:

```sh
aria2c release.torrent --dir="$OUT" --select-file=32 --seed-time=0 ...
```

A few hundred kilobytes usually completes in a minute or two even from a seeder that cannot sustain a video transfer. Apply the same approach to `Fonts.zip`, which is normally tens of megabytes and may need several attempts.

### Never wait on a dead swarm

A release that is the only one with the right subtitles is often the one nobody seeds. `SD:0` on every connection means no peer holds the data; waiting is not a plan, and a partially downloaded video is worth nothing because nothing in it can be played.

The fix is to stop treating a "release" as the unit. Split it into **video** and **subtitles** and get each from the swarm that still has it:

- Video: the most seeded release of any language, usually a Japanese-audio Blu-ray encode with English subtitles.
- Subtitles: whatever torrent, archive or pack still holds them, pulled with `--select-file` so the rest of the pack never transfers.

### The subtitle archive is often the whole release

Chinese-titled torrents frequently ship the script as a `RAR`/`ZIP` inside the file list — `[异域-11番小队]` publishes one per batch next to its videos. That archive is worth a few hundred KB and is usually the *last* thing to lose its seeds, so an SD:0 release may still hand you complete subtitles for all episodes. Look for it before concluding the release is dead:

```sh
python3 scripts/torrent_files.py release.torrent --only subtitle
aria2c release.torrent --select-file=11 --dir=/tmp/sub
unar -q -o /tmp/sub/out /tmp/sub/**/*.rar
```

Then pair the video from a seeded release with those scripts. Measure the pairing rather than assuming it: extract the seeded video's own subtitle track with `check_subs.py --extract`, and estimate its offset to the Japanese script the same way. When the Chinese↔Japanese offset matches that baseline within a second or so, the Chinese script was authored against this exact cut and only needs the baseline shift applied.

Subtitle timing comes from the Blu-ray master, so a Chinese script authored against one 1080p Blu-ray encode fits another one. Verify with `merge_bilingual.py`, which reports the offset it detected: a stable offset with a small spread means constant shift only, while a large spread means the scripts were made for different cuts. Extract the script from a finished video with `check_subs.py --extract` when the only copy lives in an embedded track.

Before abandoning partial data, check whether another torrent carries the same files — same release, different tracker or re-upload. Point that torrent at the existing directory and let aria2 hash-check it: files that are already complete are accepted and only the gaps download. See the stitching section below.

### Stitching releases

When several partial sources together cover a series, keep every file that is already complete and fetch only the holes:

```sh
python3 scripts/plan_select.py release.torrent --dir="$OUT"
```

It reports `complete` / `partial` / `missing` per file and prints the exact `--select-file=` argument for what is left, with consecutive indices collapsed into ranges. Run it against a second torrent of the same release to see whether the data already on disk can simply be adopted instead of re-downloaded.

## Stage 4 — Mux and file into Infuse

Use the library directory configured as an Infuse source, supplied by the user or by the optional personal defaults. Confirm the destination before copying files if it is unknown; Infuse has no assumed local library path here. Follow the naming convention Plex, Jellyfin, and Infuse share:

```
<library-root>/
├── Movies/<Title (Year)>/<Title (Year)>.mkv
└── TV Shows/<Title (Year)>/Season 01/<Title> - S01E01 - <Episode Title>.mkv
```

Mux the subtitle with the flags that make it appear without user interaction:

```sh
mkvmerge -o out.mkv --no-subtitles \
  --default-track 0:yes --default-track 1:no --default-track 2:yes in.mkv \
  --language 0:chi --track-name "0:中日双语" \
  --default-track 0:yes --forced-display-flag 0:yes subs/chs.ass
```

Options placed before a source apply to the next source only, and `--default-track` indices are the source file's own track IDs, so confirm them with `mkvmerge -J in.mkv` first. Verify with `python3 scripts/check_subs.py out.mkv`: the bilingual track must be `chi`, default, and forced, and its last event must fall before the video duration.

Two follow-ups worth doing without being asked:

- Install the release's fonts into `~/Library/Fonts` (`unar x Fonts.7z`, or `Keka --cli 7zz x Fonts.7z`). Without them libass falls back and Chinese/Japanese styling drifts. A truncated `Fonts.zip` downloaded partially can still be salvaged — read its entries with `zipfile` and keep whichever extract cleanly.
- Copy finished files with `cp -c` so APFS cloning avoids a second full copy.

Tell the user to set Infuse's preferred subtitle language to Chinese once, in *Settings → Playback → Subtitles*, so a track that fails to load does not fall back to the wrong language.

## Disk and duplicate hygiene

Report sizes before removing anything, and ask before deleting a release that is the only high-quality master or the only copy with a given subtitle set.

Clone-copied files share blocks with their source: deleting one of the two copies frees nothing. Measured free space only drops after both are gone. Video releases remuxed into new files are genuinely independent, so their sources can be removed for real savings. Encodes that differ only by subtitle language are redundant once a bilingual version is muxed.

## Scripts

| Script | Purpose |
| --- | --- |
| `scripts/torrent_files.py <torrent>` | List files with the index needed by `--select-file` |
| `scripts/check_subs.py <file>` | Report subtitle tracks, styles, Chinese/Japanese pairing, timing |
| `scripts/check_subs.py <file> --extract DIR` | Write a media file's text subtitle tracks out as `.ass` |
| `scripts/merge_bilingual.py --cn --jp --out` | Merge Chinese and Japanese scripts into one bilingual ASS |
| `scripts/plan_select.py <torrent> --dir DIR` | Show which files are already on disk and the `--select-file` for the rest |
