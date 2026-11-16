---
name: disk-junk-scan
description: "Scan macOS for reclaimable disk space from development tools and coding agents. Use for low disk space, caches, stale worktrees, or temporary directories. Starts read-only, returns a size-ranked table by risk tier, and requires explicit approval before cleanup."
compatibility: "Requires macOS and Python 3 with the standard library. Cleanup commands are proposed for review and run only after explicit approval."
---

# Disk Junk Scan

## Scope

Consider these development and coding-agent artifacts when removal can reclaim meaningful space.

- Ignored build and test output and dependency directories.
- Download caches and multiple versions of language toolchains.
- Git worktrees, distinguishing merged branches, clean unmerged worktrees, and worktrees with local changes.
- Project directories, directories with mktemp-style suffixes, and test caches under `/private/tmp` and `$TMPDIR`.
- Caches, logs, backups, and worktrees under `~/.codex`, `~/.claude`, `~/.cursor`, and `~/conductor`.
- Docker build cache, unused images, containers and volumes, iOS simulator devices and runtimes, and Parallels data.
- Orphaned data under `~/Library/{Containers,Application Support,Caches,Group Containers}` that cannot be matched to an installed application.

### Exclusions

Apply these exclusions to scripted scans and manual inspection.

| Exclude | Reason |
| --- | --- |
| Personal data from WeChat, QQ, Lark, browsers, mail and music apps, `Documents/Movies/Pictures`, and system directories | Inspect only if the user names them. Size alone does not make them development artifacts. |
| Measuring the `~/Library/pnpm/store` tree | Millions of hardlinks can make `du` take about 15 seconds. The action, `pnpm store prune`, does not require a size estimate. |
| OrbStack's `data.img.raw`, in-use Docker volumes, and images referenced by running containers | Use `docker system df` for reclaimable space. Never remove the backing image manually. |
| Agent sessions and configuration, such as `~/.codex/sessions` and `~/.cursor/chats` | These contain user history. |
| The default Rust toolchain and `~/.cargo/registry/cache` | Retain them. |
| Saved Application State, Preferences, UUID-named containers, and `com.apple.*` | These are small or system-owned. |
| Individual subthreshold `lib/`, `dist/`, and package-level `node_modules` entries | Group them by worktree rather than listing hundreds of small rows. |
| Whole-disk `find -size +1G` or `du` over all of `~` or `~/Library` | Measure the listed targets. Whole-tree scans can take minutes and duplicate results. |

## Workflow

1. Run one scan to produce both the size-ranked table and its JSON plan. This often takes tens of seconds and can take minutes across many repositories or on a cold disk.
2. Inspect large tier B entries using [targets.md](targets.md). Add what each item contains and who still uses it to the evidence.
3. Present free space and the tier A total first, then the tier B items that need individual approval. Offer pnpm store pruning separately if pnpm is installed.
4. After approval, show a dry run of the chosen rows before using `--execute`.
5. Report reclaimed space per row. APFS can take several minutes to reflect large deletions in `df`. Compare again if the immediate value is tens of GiB lower than expected.

### Scan once

Set `PLAN` to a new file path in the project's ignored temporary directory.

```bash
S=~/.agents/skills/disk-junk-scan/scripts
python3 "$S/scan.py" --plan "$PLAN"
```

The table goes to standard output. `--plan` writes the same rows to disk. `--json` prints JSON instead of the table. Avoid a second scan just to obtain JSON.

`scan.py` runs the machine scan (`scan_machine.py`) alongside repository scans (`scan_repo.py`) for main repositories under `--repos-root`. It combines and deduplicates the results. For one repository, use `python3 $S/scan_repo.py <repo>`.

The table columns are `# | Path | GiB | Category | Tier | Evidence | Action`. Rows are sorted by size, followed by totals for tiers A, B, and C. Each row number matches its JSON `id`, so a request to remove rows 4 and 6 maps to `--rows 4,6`. The scanner folds small directories below `--min-mib` by worktree or temporary root. A folded row records one command covering its members.

### Inspect the evidence

For tier B directories larger than 1 GiB, the evidence already includes a first-level breakdown. Inspect that breakdown instead of repeating `du` over the whole tree. Check whether the owner of an orphan container was actually uninstalled, what a `.tmp` backup contains, or whether a clean unmerged worktree has a completed PR (`gh pr list --head <branch> --state all`). Mark uncertain ownership as unknown. [Inspection commands](targets.md)

| Tier | Meaning | Approval |
| --- | --- | --- |
| A | Rebuildable at the cost of rebuild time | The user can approve the displayed tier as a batch. |
| B | Stateful, expensive to rebuild, or classified heuristically, including orphan data, clean unmerged worktrees, and recent temp directories | Obtain approval for individual rows. |
| C | Dirty worktree or path in use by a process | Report its size and leave it alone. |

- **Merged worktrees.** Check `git merge-base --is-ancestor <HEAD> <default-branch>` or whether the upstream is marked `[gone]`. Squash merges can fall into tier B. Removing a worktree retains the branch.
- **Build output.** Require a match from `git ls-files --others --ignored --directory` and verify that no tracked files reside under the path.
- **Orphan app data.** Check a reverse-domain name of at least three segments against installed bundle IDs, their first three segments, and signing teams. Also check `mdfind`. This heuristic can misclassify tools without an app bundle, so orphan data is always tier B.

### Apply an approved plan

```bash
python3 "$S/apply.py" "$PLAN" --tier A             # Preview tier A
python3 "$S/apply.py" "$PLAN" --rows 4,6 --execute # Run only the approved rows
python3 "$S/apply.py" "$PLAN" --prune-pnpm         # Preview separately authorized pnpm pruning
```

The plan is a snapshot; rescan before applying a stale plan. `apply.py` automatically enforces these execution safeguards:

- Runs each row's recorded `command` (`rm -rf`, `git worktree remove`, Docker prune, `xcrun simctl delete`, `rustup toolchain uninstall`, `npm cache clean`) from deepest path to shallowest so child worktrees are removed before parent directories.
- Verifies before each removal that the path exists, no process command line (including browsers and headless tools) references it, the worktree is clean, and no tracked files reside under it. Failed checks skip the row and report why.
- Removes members of a folded `rm -rf` row individually, retries read-only extracted directories once after `chmod -R u+w`, and never retries `Operation not permitted`.
- Skips Tier C rows and rows without automatic commands (such as Parallels data or manual model directories). Note that a Tier B parent's displayed size excludes separately listed children, but approving the parent removes the entire parent tree.

When `rm -rf` succeeds and the path disappears, use the planned size. Measure again only if some of the tree remains. For tool commands, use the amount the tool reports. Compare available space with `df` after execution.

## Manual cleanup

When cleaning up outside `apply.py`, follow the store rules and inspection commands in [targets.md](targets.md):

- Prefer the tool's own cleanup command. Use `rm -rf` only for disposable output and temporary directories.
- Run `pnpm store prune` only when explicitly selected by the user.
- Immediately before removal, recheck `git status --porcelain`, `git ls-files -- <path>`, and `ps -axo command`. Require a clean tree, no tracked files under the path, and no process using it.
- After cleanup, confirm that active projects retain their `node_modules` and that `docker system df` agrees with the expected result.

## Scripts

| File | Responsibility |
| --- | --- |
| `scripts/scan.py` | Run machine and repository scans in parallel, then produce one table and JSON plan. |
| `scripts/apply.py` | Recheck and apply selected rows, with a separate `--prune-pnpm` option. Defaults to dry run. |
| `scripts/scan_machine.py` | Inspect known caches, toolchains, Docker, simulators, agent directories, temporary directories, and orphan app data. The installed-app index is cached under `~/.cache/disk-junk-scan/`. |
| `scripts/scan_repo.py` | Classify worktrees, ignored artifacts and dependencies, and temporary directories named for the repository. |
| `scripts/common.py` | Share the `Row` format (including `command`, `members`, and `id`), batched `du`, folding, deduplication, and table rendering. |

The scripts use the Python 3 standard library, batching `du` and `git ls-files` per worktree and scanning repositories concurrently.
