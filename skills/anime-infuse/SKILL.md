---
name: anime-infuse
description: "Acquire anime films and series with bilingual Chinese/Japanese subtitles and file them into an Infuse library. Use when the user asks to download anime, wants 中日双语 or 简日双语 subtitles, asks for a season batch from Mikan or Nyaa, needs subtitles rescued from a torrent with no seeders, or wants finished media imported and readable in Infuse."
compatibility: "macOS with aria2c, mkvmerge, ffprobe, and python3. Sites used for searching and subtitles are external and can change or rate-limit."
---

# Anime Infuse

Turn "I want this show with Chinese-Japanese subtitles on my Apple devices" into playable files. Four stages, each with a verification step, because most failures here are silent: a torrent that looks alive, subtitles that turn out to be monolingual, or files that Infuse cannot match.

Respond in Chinese unless the user writes in another language.

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

## Stage 4 — Mux and file into Infuse

Infuse reads a local folder tree; on macOS its configured source is `~/Movies/Infuse`. Follow the naming convention Plex, Jellyfin, and Infuse share:

```
~/Movies/Infuse/
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