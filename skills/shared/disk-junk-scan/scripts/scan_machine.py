#!/usr/bin/env python3
"""Read-only machine-level scan limited to developer / coding-agent data.

Covers tool caches, package stores, toolchains, Docker, iOS Simulator, agent
workspaces, temp dirs, and orphaned app data whose owning app is gone.
Personal application data (chat, browser, media) is deliberately skipped, and
rows that could never be acted on are not emitted.

Usage: scan_machine.py [--min-mib N] [--json]
"""
import argparse
import json
import os
import re
import shutil
import sys
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (HOME, MKTEMP_SUFFIX, Row, annotate_breakdown, dedupe, du_many, entries, fold_small, gib,  # noqa: E402
                    is_git_dirty, mtime_days, parse_human_size_kib, parse_reported_free_kib, render_table,
                    rm_command, run)

L = f"{HOME}/Library"
CACHE_DIR = f"{HOME}/.cache/disk-junk-scan"

# (path, category, tier, evidence, action). Only actionable entries; sizes measured at scan time.
# apply.py runs `rm -rf <path>` unless the path has an entry in TOOL_COMMANDS.
FIXED = [
    (f"{L}/Developer/Xcode/DerivedData", "Xcode build intermediates", "A", "Rebuildable", "Remove"),
    (f"{L}/Developer/Xcode/iOS DeviceSupport", "Device symbols", "B", "One set per iOS version", "Remove older versions"),
    (f"{L}/Developer/Xcode/Archives", "Xcode archives", "B", "May contain release builds", "Confirm before removal"),
    (f"{L}/Developer/CoreSimulator/Caches", "Simulator caches", "A", "Rebuildable", "Remove"),
    (f"{L}/Android/sdk/system-images", "Android emulator images", "B", "Expensive to download again", "Remove unused API levels"),
    (f"{HOME}/.android/avd", "Android virtual devices", "B", "Device data", "Remove unused devices"),
    (f"{HOME}/.gradle/caches", "Gradle cache", "A", "Can be downloaded again", "Remove"),
    (f"{HOME}/.gradle/daemon", "Gradle daemon logs", "A", "Logs", "Remove"),
    (f"{HOME}/.m2/repository", "Maven repository", "B", "Slow to download again", "Confirm before removal"),
    (f"{HOME}/go/pkg/mod", "Go module cache", "B", "Slow to download again", "`go clean -modcache`"),
    (f"{HOME}/.npm/_cacache", "npm cache", "A", "Can be downloaded again", "`npm cache clean --force`"),
    (f"{HOME}/.yarn/berry/cache", "Yarn cache", "A", "Can be downloaded again", "`yarn cache clean`"),
    (f"{HOME}/.bun/install/cache", "Bun cache", "A", "Can be downloaded again", "`bun pm cache rm`"),
    (f"{L}/Caches/pnpm", "pnpm download cache", "A", "Can be downloaded again", "Remove"),
    # ~/Library/pnpm/store is deliberately absent: du over millions of hardlinks costs ~15 s
    # and the only valid action (`pnpm store prune`) does not depend on knowing its size.
    (f"{HOME}/.cargo/registry/src", "Unpacked Cargo source", "A", "Can be unpacked again from cache/", "Remove"),
    (f"{HOME}/.cargo/git", "Cargo Git dependencies", "B", "Requires a fresh clone", "Confirm before removal"),
    (f"{HOME}/.cache/uv", "uv cache", "B", "Slow to download again", "`uv cache prune`"),
    (f"{HOME}/.cache/pip", "pip cache", "A", "Can be downloaded again", "`pip cache purge`"),
    (f"{HOME}/.cache/huggingface", "Hugging Face model cache", "B", "Models are slow to download again", "Confirm before removal"),
    (f"{HOME}/.cache/modelscope", "ModelScope model cache", "B", "Models are slow to download again", "Confirm before removal"),
    (f"{HOME}/.ollama/models", "Ollama models", "B", "Model files", "`ollama rm`"),
    (f"{HOME}/.lmstudio", "LM Studio models", "B", "Model files", "Remove in the app"),
    (f"{HOME}/.cache/codex-runtimes", "Codex runtimes", "A", "Codex downloads these again automatically", "Remove"),
    (f"{L}/Caches/ms-playwright", "Playwright browsers", "A", "Download again with `npx playwright install`", "Remove"),
    (f"{L}/Caches/Homebrew", "Homebrew downloads", "A", "`brew cleanup` removes outdated bottles only. The initial size covers the whole cache", "`brew cleanup`"),
    (f"{L}/Caches/CocoaPods", "CocoaPods cache", "A", "Can be downloaded again", "Remove"),
    (f"{L}/Caches/org.swift.swiftpm", "SwiftPM cache", "A", "Can be downloaded again", "Remove"),
    (f"{L}/Caches/go-build", "Go build cache", "A", "Rebuildable", "`go clean -cache`"),
    (f"{L}/Caches/node-gyp", "node-gyp headers", "A", "Can be downloaded again", "Remove"),
    (f"{L}/Caches/typescript", "TypeScript automatic type acquisition", "A", "Can be downloaded again", "Remove"),
    (f"{L}/Caches/electron", "Electron binaries", "A", "Can be downloaded again", "Remove"),
    (f"{L}/Caches/electron-builder", "electron-builder cache", "A", "Can be downloaded again", "Remove"),
    (f"{L}/Caches/JetBrains", "JetBrains IDE caches", "A", "Indexes can be rebuilt", "Close the IDE before removal"),
    (f"{L}/Caches/Codex", "Codex cache", "A", "Rebuildable", "Remove"),
    (f"{L}/Caches/dotslash", "dotslash cache", "A", "Can be downloaded again", "Remove"),
    (f"{L}/Caches/cursor-compile-cache", "Cursor compile cache", "A", "Rebuildable", "Remove"),
    (f"{L}/Application Support/Code/Cache", "VS Code cache", "A", "Rebuildable", "Remove"),
    (f"{L}/Application Support/Code/CachedData", "VS Code cache", "A", "Rebuildable", "Remove"),
    (f"{L}/Application Support/Cursor/Cache", "Cursor cache", "A", "Rebuildable", "Remove"),
    (f"{L}/Application Support/Cursor/CachedData", "Cursor cache", "A", "Rebuildable", "Remove"),
    (f"{L}/Application Support/Zed", "Zed data", "B", "Contains language servers and extensions", "Confirm before removing subdirectories"),
    (f"{L}/Application Support/JetBrains", "JetBrains settings and plugins", "B", "Contains plugins and indexes", "Remove only old version directories"),
    (f"{HOME}/Parallels", "Parallels VM", "B", "Entire virtual machine", "Compact or move in Parallels"),
]
# Paths whose owning tool has a proper cleanup command; None = must be done by hand.
TOOL_COMMANDS = {
    f"{HOME}/go/pkg/mod": ["go", "clean", "-modcache"],
    f"{HOME}/.npm/_cacache": ["npm", "cache", "clean", "--force"],
    f"{HOME}/.yarn/berry/cache": ["yarn", "cache", "clean"],
    # bun's `pm cache rm` only works inside a project; plain rm -rf is what it does anyway
    f"{HOME}/.cache/uv": ["uv", "cache", "prune"],
    f"{HOME}/.cache/pip": ["pip", "cache", "purge"],
    f"{L}/Caches/Homebrew": ["brew", "cleanup"],
    f"{L}/Caches/go-build": ["go", "clean", "-cache"],
    f"{HOME}/.ollama/models": None,
    f"{HOME}/.lmstudio": None,
    f"{L}/Application Support/Zed": None,
    f"{L}/Application Support/JetBrains": None,
    f"{HOME}/Parallels": None,
    f"{L}/Developer/Xcode/iOS DeviceSupport": None,
    f"{L}/Android/sdk/system-images": None,
    f"{HOME}/.android/avd": None,
}
VERSION_MANAGERS = [
    (f"{HOME}/.local/share/fnm/node-versions", "Node versions (fnm)", ["fnm", "uninstall"]),
    (f"{HOME}/.nvm/versions/node", "Node versions (nvm)", None),  # nvm is a shell function
    (f"{HOME}/.gvm/gos", "Go versions (gvm)", None),
    (f"{HOME}/.g/versions", "Go versions (g)", ["g", "uninstall"]),
    (f"{HOME}/.pyenv/versions", "Python versions (pyenv)", ["pyenv", "uninstall", "-f"]),
]
AGENT_ROOTS = [f"{HOME}/.codex", f"{HOME}/.claude", f"{HOME}/.cursor", f"{HOME}/.conductor", f"{HOME}/conductor"]
AGENT_CACHE_NAMES = {"cache", "log", "logs", "shell_snapshots", "debug", "generated_images"}
AGENT_BACKUP_NAMES = {"tmp", ".tmp"}
TEMP_ROOTS = ["/private/tmp", os.environ.get("TMPDIR", "")]
DEV_MARKERS = {".git", "package.json", "Cargo.toml", "pyproject.toml", "go.mod", "node_modules", "target", "pnpm-lock.yaml"}
TEST_CACHE_PREFIXES = ("node-compile-cache", "metro-cache", "v8-compile-cache", "tsx-", "jest_", "vitest-",
                       "cargo-install", "pip-", "uv-", "pnpm-", "turbo", "esbuild", "playwright")
APP_ROOTS = ["/Applications", "/Applications/Setapp", "/Applications/Utilities", f"{HOME}/Applications",
             "/System/Applications", "/System/Applications/Utilities", "/System/Library/CoreServices"]
REVERSE_DNS = re.compile(r"^[A-Za-z0-9-]+(\.[A-Za-z0-9_-]+){2,}$")
TEAM_PREFIX = re.compile(r"^[A-Z0-9]{10}\.")
UUID_NAME = re.compile(r"^[0-9A-F]{8}-[0-9A-F]{4}-", re.I)


def rows_from(specs):
    """specs: (path, category, tier, evidence, action[, command]); sizes measured in one pass.

    Command defaults to `rm -rf path`, overridden by TOOL_COMMANDS; tier C never gets one.
    """
    specs = [s for s in specs if os.path.exists(s[0])]
    sizes = du_many([s[0] for s in specs])
    rows = []
    for spec in specs:
        path, cat, tier, ev, act = spec[:5]
        if len(spec) > 5:
            command = spec[5]
        elif tier == "C":
            command = None
        else:
            command = TOOL_COMMANDS.get(path, rm_command(path))
        rows.append(Row(path, sizes.get(path, 0), cat, tier, ev, act, command=command or []))
    return rows


def rustup_default():
    """Default toolchain name from settings.toml (running `rustup` costs seconds)."""
    try:
        with open(f"{HOME}/.rustup/settings.toml") as fh:
            m = re.search(r'^default_toolchain\s*=\s*"([^"]+)"', fh.read(), re.M)
            return m.group(1) if m else ""
    except OSError:
        return ""


def toolchain_specs():
    default = rustup_default()  # e.g. stable-aarch64-apple-darwin
    for e in entries(f"{HOME}/.rustup/toolchains"):
        if e.name != default:
            yield (e.path, "Rust toolchain", "B", "Non-default toolchain", "`rustup toolchain uninstall`",
                   ["rustup", "toolchain", "uninstall", e.name])
    for root, cat, cmd in VERSION_MANAGERS:
        for e in entries(root):
            if e.is_dir(follow_symlinks=False):
                yield (e.path, cat, "B", "Multiple versions installed", f"`{cmd[0]} uninstall`" if cmd else "Uninstall with the version manager",
                       [*cmd, e.name] if cmd else None)


def docker_rows():
    rows = []
    for line in run(["docker", "system", "df", "--format", "{{json .}}"], timeout=60).splitlines():
        try:
            d = json.loads(line)
        except ValueError:
            continue
        reclaim = parse_human_size_kib(d.get("Reclaimable", "0B").split(" ")[0])
        if not reclaim:
            continue  # nothing to act on
        kind, n, active = d.get("Type", ""), d.get("TotalCount"), d.get("Active")
        if kind == "Build Cache":
            rows.append(Row("docker://build-cache", reclaim, "Docker build cache", "A", f"{n} layers total",
                            "`docker builder prune -af`", command=["docker", "builder", "prune", "-af"]))
        elif kind == "Images":
            rows.append(Row("docker://images-unused", reclaim, "Unused Docker images", "B", f"{n} images, {active} in use",
                            "`docker image prune -a`", command=["docker", "image", "prune", "-af"]))
        elif kind == "Containers":
            rows.append(Row("docker://containers-stopped", reclaim, "Stopped Docker containers", "B", f"{n} containers, {active} running",
                            "`docker container prune`", command=["docker", "container", "prune", "-f"]))
        elif kind == "Local Volumes":
            rows.append(Row("docker://volumes-unused", reclaim, "Unused Docker volumes", "B", f"{n} volumes, {active} in use",
                            "`docker volume prune`", command=["docker", "volume", "prune", "-f"]))
    return rows


def simulator_rows():
    rows = []
    try:
        runtimes = json.loads(run(["xcrun", "simctl", "runtime", "list", "-j"], timeout=60) or "{}")
        devices = json.loads(run(["xcrun", "simctl", "list", "devices", "-j"], timeout=60) or "{}").get("devices", {})
    except ValueError:
        return rows
    for rt in runtimes.values():
        platform = rt.get("platformIdentifier", "").split(".")[-1].replace("simulator", "")
        rows.append(Row(f"simctl-runtime://{rt['identifier']}", int(rt.get("sizeBytes", 0)) // 1024,
                        "Simulator runtime", "B", f"{platform} {rt.get('version')}, {rt.get('state')}",
                        f"`xcrun simctl runtime delete {rt['identifier']}` (when no devices use it)",
                        command=["xcrun", "simctl", "runtime", "delete", rt["identifier"]]))
    devs = [(d, rid) for rid, lst in devices.items() for d in lst if os.path.isdir(d.get("dataPath", ""))]
    sizes = du_many([d["dataPath"] for d, _ in devs])
    for d, rid in devs:
        label = f"{d['name']} / {rid.rsplit('.', 1)[-1]}"
        if d.get("isAvailable", True):
            rows.append(Row(d["dataPath"], sizes[d["dataPath"]], "Simulator device", "B", f"{label}, {d.get('state')}",
                            "`xcrun simctl delete <udid>`", command=["xcrun", "simctl", "delete", d["udid"]]))
        else:
            rows.append(Row(d["dataPath"], sizes[d["dataPath"]], "Orphan simulator device", "A", f"{label}, runtime no longer installed",
                            "`xcrun simctl delete unavailable`", command=["xcrun", "simctl", "delete", "unavailable"]))
    return rows


def git_dir_spec(path, category, prefix=""):
    dirty = is_git_dirty(path)
    days = mtime_days(path)
    if dirty:
        return (path, category, "C", f"{prefix}uncommitted Git changes, modified {days} days ago", "Leave in place")
    if dirty is False:
        return (path, category, "B", f"{prefix}clean worktree, modified {days} days ago", "Confirm the branch has merged before removal")
    return (path, category, "B", f"{prefix}modified {days} days ago", "Confirm before removal")


def agent_specs():
    """Caches, backups and worktrees under agent homes. Session/config dirs are not junk and are skipped."""
    for root in AGENT_ROOTS:
        for e in entries(root):
            if not e.is_dir(follow_symlinks=False):
                continue
            label = f"`{os.path.basename(root)}/{e.name}`"
            if e.name == "worktrees":
                for wt in entries(e.path):
                    if wt.is_dir(follow_symlinks=False):
                        yield git_dir_spec(wt.path, "agent worktree")
            elif e.name in AGENT_CACHE_NAMES:
                yield (e.path, "Agent cache/logs", "A", label, "Remove")
            elif e.name in AGENT_BACKUP_NAMES:
                names = {c.name for c in entries(e.path)}
                session_copy = any(
                    n in {"sessions", "archived_sessions"} or n.endswith(".sqlite")
                    for n in names
                )
                note = ", contains session backups" if session_copy else " (includes history backups)"
                yield (e.path, "Agent temporary files/backups", "B", label + note, "Inspect contents before removal")


def temp_rows(min_kib):
    """Developer-looking dirs under each temp root; small ones folded into one row per root."""
    rows, seen = [], set()
    for root in TEMP_ROOTS:
        root = os.path.realpath(root) if root else ""
        if not root or root in seen or not os.path.isdir(root):
            continue
        seen.add(root)
        rows.extend(fold_small(rows_from(list(temp_specs(root))), min_kib, root))
    return rows


def temp_specs(root):
    for e in entries(root):
        if not e.is_dir(follow_symlinks=False) or "com.apple." in e.name:
            continue
        names = {c.name for c in entries(e.path)}
        dev = bool(names & DEV_MARKERS)
        test_cache = e.name.startswith(TEST_CACHE_PREFIXES)
        mk = bool(MKTEMP_SUFFIX.search(e.name))
        # A bundle id whose last label merely looks random is an app temp dir, not a project mktemp.
        if not dev and not test_cache and REVERSE_DNS.match(e.name):
            continue
        if not (dev or test_cache or mk):
            continue  # not developer-related; out of scope
        why = ", ".join(w for w, ok in (("Contains project files", dev), ("Test cache", test_cache), ("mktemp suffix", mk)) if ok)
        days = mtime_days(e.path)
        if ".git" in names:
            yield git_dir_spec(e.path, "Temporary directory", why + ", ")
        elif days is not None and days < 1:
            yield (e.path, "Temporary directory", "B", f"{why}, modified within the last 24 hours", "Confirm before removal")
        else:
            yield (e.path, "Temporary directory", "A", f"{why}, modified {days} days ago", "Remove")


def installed_apps():
    """Bundle ids and signing team ids of installed .app bundles, cached until an app root changes."""
    stamp = [os.lstat(r).st_mtime for r in APP_ROOTS if os.path.isdir(r)]
    cache_file = f"{CACHE_DIR}/apps.json"
    try:
        with open(cache_file) as fh:
            cached = json.load(fh)
        if cached.get("stamp") == stamp:
            return set(cached["ids"]), set(cached["teams"])
    except (OSError, ValueError, KeyError):
        pass
    ids, teams = set(), set()
    for root in APP_ROOTS:
        for e in entries(root):
            if not e.name.endswith(".app"):
                continue
            bid = run(["plutil", "-extract", "CFBundleIdentifier", "raw", "-o", "-", f"{e.path}/Contents/Info.plist"], timeout=10).strip()
            if bid:
                ids.add(bid)
            # Reason: codesign prints its report on stderr.
            m = re.search(r"TeamIdentifier=([A-Z0-9]{10})", run(["codesign", "-d", "--verbose=2", e.path], timeout=10, merge_stderr=True))
            if m:
                teams.add(m.group(1))
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(cache_file, "w") as fh:
            json.dump({"stamp": stamp, "ids": sorted(ids), "teams": sorted(teams)}, fh)
    except OSError:
        pass
    return ids, teams


def app_known(bundle_id, ids):
    """Cheap in-memory check: exact id, or same 3-label product prefix (helpers, extensions)."""
    if bundle_id in ids:
        return True
    prefix = ".".join(bundle_id.split(".")[:3])
    return any(i == prefix or i.startswith(prefix + ".") for i in ids)


def app_on_disk(bundle_id):
    return bool(run(["mdfind", f"kMDItemCFBundleIdentifier == '{bundle_id}'"], timeout=15).strip())


def orphan_rows(min_kib):
    """App data whose owning app is no longer installed. Heuristic; always tier B.

    Order of checks is cheapest first: in-memory id/team match, then `du` (batched),
    then `mdfind` only for entries that are both unmatched and large enough to matter.
    """
    ids, teams = installed_apps()
    unknown = []  # (path, bundle_id, label)
    for root, label in ((f"{L}/Containers", "Container"), (f"{L}/Application Support", "Application Support"), (f"{L}/Caches", "Cache")):
        for e in entries(root):
            n = e.name
            if UUID_NAME.match(n) or not REVERSE_DNS.match(n) or "com.apple." in n or app_known(n, ids):
                continue
            unknown.append((e.path, n, f"{label}, no installed app found for `{n}`"))
    for e in entries(f"{L}/Group Containers"):
        m = TEAM_PREFIX.match(e.name)
        if not m or "com.apple." in e.name or m.group(0)[:-1] in teams:
            continue
        rest = e.name[len(m.group(0)):]
        rest = rest[6:] if rest.startswith("group.") else rest
        if not app_known(rest, ids):
            unknown.append((e.path, rest, f"Group Container, no installed app for team `{m.group(0)[:-1]}`"))
    sizes = du_many([p for p, _, _ in unknown])
    rows = []
    for path, bid, evidence in unknown:
        if sizes.get(path, 0) >= min_kib and not app_on_disk(bid):
            rows.append(Row(path, sizes[path], "Orphan application data", "B", evidence, "Confirm the app is uninstalled before removal", command=rm_command(path)))
    return rows


def capacity_line():
    out = run(["df", "-k", "/System/Volumes/Data"]).splitlines()
    if len(out) < 2:
        return ""
    f = out[1].split()
    return f"Data volume {int(f[1]) / 1048576:.0f} GiB, {f[4]} used, **{int(f[3]) / 1048576:.1f} GiB** available (read-only scan)"


def annotate_tool_reclaim(rows):
    """Directory size is not reclaimable when the command only prunes.

    `brew cleanup -n` prints the amount it would free. `uv cache prune` has no
    dry-run, so its directory stays visible but does not enter the tier total.
    """
    for row in rows:
        if row.command == ["brew", "cleanup"] and shutil.which("brew"):
            out = run(["brew", "cleanup", "-n"], timeout=180, merge_stderr=True)
            reclaim = parse_reported_free_kib(out) or 0
            row.evidence += f" (directory {gib(row.size_kib)} GiB, cleanup estimates {gib(reclaim)} GiB reclaimable)"
            row.size_kib = reclaim
            row.reclaim_kib = reclaim
        elif row.command[:3] == ["uv", "cache", "prune"]:
            row.evidence += " (prune provides no estimate, so the directory size is excluded from totals)"
            row.reclaim_kib = 0
    return rows


def collect(min_kib):
    # Reason: every collector is dominated by waiting on du/docker/simctl, so they overlap well.
    jobs = [
        lambda: rows_from(FIXED),
        lambda: rows_from(list(toolchain_specs()) + list(agent_specs())),
        lambda: temp_rows(min_kib),
        docker_rows,
        simulator_rows,
        lambda: orphan_rows(min_kib),
    ]
    rows = []
    with ThreadPoolExecutor(max_workers=len(jobs)) as pool:
        for result in pool.map(lambda job: job(), jobs):
            rows.extend(result)
    return annotate_tool_reclaim(rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--min-mib", type=int, default=20, help="hide rows smaller than this (default 20)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    rows = annotate_breakdown(dedupe(collect(args.min_mib * 1024)))
    if args.json:
        print(json.dumps([r.as_dict() for r in rows], ensure_ascii=False, indent=2))
    else:
        print(render_table(rows, args.min_mib * 1024, capacity_line()))


if __name__ == "__main__":
    main()
