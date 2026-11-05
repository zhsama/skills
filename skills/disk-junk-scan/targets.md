# Inspection commands and classification criteria

Use these checks to identify the owner of large tier B and C items after the scanner reports them. Run cleanup commands only for approved targets.

## Capacity

```bash
df -h / /System/Volumes/Data      # GiB
df -H /System/Volumes/Data        # Decimal GB, closer to the menu bar display
diskutil info / | grep -Ei 'Free Space|Purgeable'
tmutil listlocalsnapshots /
```

Menu bar tools that report decimal GB and include purgeable space can show values over 7% higher than `df -h`.

## Git worktrees

```bash
git -C <repo> worktree list --porcelain
git -C <wt> status --porcelain --untracked-files=all          # Empty output means clean
git -C <repo> merge-base --is-ancestor <wt-HEAD> main && echo merged
git -C <repo> for-each-ref --format='%(refname:short) %(upstream:track)' refs/heads   # [gone] means the upstream was removed
gh pr list --repo <owner/repo> --head <branch> --state all    # Check squash merges here
git -C <repo> worktree remove <path>                          # Only after approval. Use worktree prune for a missing directory.
```

## Build artifacts and dependencies

```bash
git -C <wt> ls-files -z --others --ignored --exclude-standard --directory | tr '\0' '\n'
git -C <wt> ls-files -- <rel>          # Any output means the path contains tracked files
ps -axo command | grep <path>
```

- A Rust `target/` can exceed 40 GB in one repository, with a separate copy in each worktree.
- Mobile build paths include `android/app/build`, `ios/build`, `ios/Pods`, and `.cxx`.
- Sample ordinary files in pnpm's `node_modules` and inspect `st_nlink`. A link count above one means removing the directory does not reclaim the copy in the store. A count of one indicates an independent copy whose space is measured by `du` and whose dependencies must be reinstalled. In either case run `pnpm store prune` during approved cleanup.

## Temporary directories

```bash
ls -la /private/tmp "$TMPDIR"
stat -f '%Sm %N' -t '%F' /private/tmp/*            # Modification time
cat <dir>/.git                                     # A file containing gitdir: identifies a linked worktree
```

- Look for names such as `<project>-<issue-number>-(validation|ablation|perf|bin|cli|tools).<mktemp-suffix>`.
- Under `$TMPDIR`, `node-compile-cache`, `metro-cache`, `v8-compile-cache-*`, `tsx-*`, `jest_*`, and `vitest-*` are tier A build or test caches.
- A name with neither project files nor a mktemp suffix can belong to another application. Leave it out.
- Exclude `com.apple.*` and reverse-domain names that match only because the last segment resembles a mktemp suffix, such as `com.apple.Safari` and `dev.kdrag0n.MacVirt`.
- Measure the last 24 hours by modification time.
- For tier B directories larger than 1 GiB, the evidence includes the largest children from `du -d 1`. Use it rather than remeasuring the entire tree.

## Agent directories

| Path | Contents | Tier |
| --- | --- | --- |
| `~/.codex/{cache,tmp,log,shell_snapshots,worktrees}` and `~/.cache/codex-runtimes` | Caches, logs, and worktrees | A for caches and logs. Check Git state for worktrees. |
| `~/.codex/{sessions,archived_sessions,history.jsonl,*.sqlite}` and copies under `.tmp` containing `codex-history-original-backup-*`, `sessions`, `archived_sessions`, or `*.sqlite` | Session history and backups | C for active history. Classify the enclosing backup directory as B and inspect it. When `~/.codex/sessions` still exists, the backup is a separate copy. |
| `~/.claude/{cache,debug}` | Caches | A |
| `~/.claude/projects` | Sessions | C |
| `~/.cursor/{worktrees,projects}` | Worktrees and sessions | Check Git state for worktrees. Sessions are C. |
| `~/conductor/workspaces/*` | One clone per directory | Check Git state. |

## Docker and OrbStack

```bash
docker system df -v
docker ps -a --size --format 'table {{.Names}}\t{{.Status}}\t{{.Size}}\t{{.Image}}'
docker volume ls
docker volume inspect <vol> --format '{{.Labels}}'      # The labels identify the Compose project
docker image inspect <img> --format '{{index .Config.Labels "org.opencontainers.image.source"}}'
```

Build cache is tier A. Unused images and stopped containers are B. Unreferenced volumes are also B because they may contain a former project's database. Items referenced by running containers are C.

OrbStack's `~/Library/Group Containers/HUAQ24HBR6.dev.orbstack/data/data.img.raw` is sparse. The 8T shown by `ls -l` is a logical size. Use Docker prune commands for approved cleanup and leave the backing file intact.

## iOS simulators

```bash
xcrun simctl runtime list -j          # Inspect sizeBytes and deletable
xcrun simctl list devices -j          # isAvailable=false identifies devices whose runtime is missing
xcrun simctl delete unavailable       # Removes only unavailable devices, after approval
xcrun simctl delete <udid>
xcrun simctl runtime delete <identifier>
```

## Toolchain versions

```bash
rustup toolchain list                 # Look for the (default) marker
fnm list
nvm ls
gvm list
pyenv versions
```

Non-default versions that have not been used recently are tier B.

## Orphan application data

```bash
plutil -extract CFBundleIdentifier raw -o - /Applications/X.app/Contents/Info.plist
codesign -d --verbose=2 /Applications/X.app 2>&1 | grep TeamIdentifier      # Prefix used in Group Containers
mdfind "kMDItemCFBundleIdentifier == 'com.foo.bar'"                        # Search for the bundle
ls -la ~/Library/Containers/<bundle>/Data                                   # Inspect contents
```

For a reverse-domain directory, check its bundle ID, first three name segments, and signing team against installed apps. Require an empty `mdfind` result as well. The scan checks `/Applications` (including Setapp and Homebrew cask apps), `~/Applications`, and `/System/Applications`. Command-line tools without app bundles can look orphaned, so these candidates remain tier B.

## Shared stores

| Path | Handling |
| --- | --- |
| `~/Library/pnpm/store` | Skip the roughly 15-second `du`. Use `pnpm store prune` during cleanup and check that active projects still have their `node_modules`. |
| `~/Library/Caches/Homebrew` | Use `brew cleanup -n` for estimated reclaimed space. With `brew cleanup -s`, even current bottles will be downloaded again on the next install. |
| `~/.cache/uv` | `uv cache prune` has no dry run. Exclude the directory size from totals and use the amount reported at execution. |
| `~/.cargo/registry/src` | Can be unpacked again from `cache/`. |
| `~/.cargo/registry/cache` | Retain and omit from the table. |
| `~/go/pkg/mod` | Use `go clean -modcache`. |
