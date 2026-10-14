#!/usr/bin/env python3
"""Read-only scan of one git repository for reclaimable disk usage.

Emits rows for: linked worktrees (removable / confirm), git-ignored build and
dependency directories, and temp/validation directories named after the project.
Never modifies anything.

Usage: scan_repo.py REPO [--name PROJECT] [--min-mib N] [--json]
"""
import argparse
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (HOME, MKTEMP_SUFFIX, Row, age_days, du_many, entries, fold_small, git,  # noqa: E402
                    is_git_dirty, render_table, rm_command, run)

BUILD_NAMES = {
    "target", "dist", "build", "lib", "out", ".next", ".turbo", ".nuxt", ".svelte-kit",
    "coverage", ".nyc_output", ".eslintcache", ".jest-cache", ".pytest_cache", ".mypy_cache",
    ".ruff_cache", "__pycache__", ".tmp", "tmp", "__typecheck__", "test.lib", ".verdaccio-cache",
    "DerivedData", ".gradle", ".parcel-cache", ".cache", "storybook-static", ".cxx",
}
BUILD_SUFFIXES = (".tsbuildinfo",)
DEP_NAMES = {"node_modules", ".venv", "venv", "Pods", ".pnpm-store", "vendor", ".yarn"}
PROCESS_HINTS = ("cargo", "rustc", "rust-analyzer", "jest", "vitest", "node", "pnpm", "tsc", "python")
TEMP_ROOTS = ["/private/tmp", os.environ.get("TMPDIR", ""),
              f"{HOME}/.codex/worktrees", f"{HOME}/.cursor/worktrees", f"{HOME}/conductor/workspaces"]
DEFAULT_MIN_KIB = 20 * 1024


def default_branch(repo):
    ref = git(["symbolic-ref", "-q", "refs/remotes/origin/HEAD"], repo).strip()
    if ref:
        return ref.rsplit("/", 1)[-1]
    for name in ("main", "master", "develop"):
        if git(["rev-parse", "-q", "--verify", f"refs/heads/{name}"], repo).strip():
            return name
    return "HEAD"


def list_worktrees(repo):
    """Parse `git worktree list --porcelain`; the first entry is the main worktree."""
    result = []
    for block in git(["worktree", "list", "--porcelain"], repo).strip().split("\n\n"):
        if not block.strip():
            continue
        wt = {"path": "", "head": "", "branch": "", "detached": False, "main": False}
        for line in block.splitlines():
            key, _, value = line.partition(" ")
            if key == "worktree":
                wt["path"] = value
            elif key == "HEAD":
                wt["head"] = value
            elif key == "branch":
                wt["branch"] = value.replace("refs/heads/", "")
            elif key == "detached":
                wt["detached"] = True
        result.append(wt)
    if result:
        result[0]["main"] = True
    return result


def running_commands():
    """Command lines of all processes except this scanner and its parent shell."""
    own = {str(os.getpid()), str(os.getppid())}
    commands = []
    for line in run(["ps", "-axo", "pid=,command="]).splitlines():
        pid, _, cmd = line.strip().partition(" ")
        if cmd and pid not in own and "scan_" not in cmd:
            commands.append(cmd)
    return commands


def processes_using(path, commands):
    # Reason: lsof over a large worktree is too slow; a command-line substring match
    # catches cargo/jest/node processes launched from the directory.
    return [c for c in commands if path in c and any(h in c for h in PROCESS_HINTS)]


def is_merged(repo, head, default):
    if not head or default == "HEAD":
        return False
    try:
        return subprocess.run(["git", "-C", str(repo), "merge-base", "--is-ancestor", head, default],
                              capture_output=True, check=False, timeout=60).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def upstream_gone(repo, branch):
    if not branch:
        return False
    track = git(["for-each-ref", "--format=%(upstream:track)", f"refs/heads/{branch}"], repo).strip()
    return track == "[gone]"


def worktree_rows(repo, worktrees, default, commands):
    linked = [wt for wt in worktrees if not wt["main"]]
    sizes = du_many([wt["path"] for wt in linked if os.path.isdir(wt["path"])])
    rows = []
    for wt in linked:
        path = wt["path"]
        label = wt["branch"] or ("detached " + wt["head"][:8])
        remove = ["git", "-C", repo, "worktree", "remove", path]
        if not os.path.isdir(path):
            rows.append(Row(path, 0, "worktree", "A", f"`{label}` 目录已不存在", "`git worktree prune`",
                            command=["git", "-C", repo, "worktree", "prune"]))
            continue
        dirty = is_git_dirty(path)
        in_use = processes_using(path, commands)
        ts = git(["log", "-1", "--format=%ct"], path).strip()
        days = age_days(int(ts)) if ts.isdigit() else "?"
        size = sizes.get(path, 0)
        base = f"`{label}`，最后提交 {days} 天前"
        if dirty:
            rows.append(Row(path, size, "worktree", "C", base + "，有未提交改动", "不动"))
        elif in_use:
            rows.append(Row(path, size, "worktree", "C", base + f"，{len(in_use)} 个进程在用", "不动"))
        elif is_merged(repo, wt["head"], default):
            rows.append(Row(path, size, "worktree", "A", base + f"，干净，已并入 `{default}`",
                            "`git worktree remove`（分支保留）", command=remove))
        elif upstream_gone(repo, wt["branch"]):
            rows.append(Row(path, size, "worktree", "A", base + "，干净，上游分支已删除",
                            "`git worktree remove`（分支保留）", command=remove))
        else:
            rows.append(Row(path, size, "worktree", "B", base + "，干净但未并入（可能 squash merge）",
                            "`gh pr list --head` 确认后 `git worktree remove`", command=remove))
    return rows


def tracked_dirs(wt_path):
    """Every directory that contains at least one tracked file (relative paths)."""
    dirs = set()
    for rel in git(["ls-files", "-z"], wt_path).split("\0"):
        while "/" in rel:
            rel = rel.rsplit("/", 1)[0]
            if rel in dirs:
                break
            dirs.add(rel)
    return dirs


def artifact_rows(wt_path, min_kib):
    """Git-ignored build/test artifacts (A) and dependency dirs (B) inside one worktree.

    Entries smaller than min_kib are folded into one aggregate row per tier so a
    monorepo with hundreds of tiny lib/ and dist/ dirs yields two rows, not hundreds.
    """
    out = run(["git", "-C", wt_path, "ls-files", "-z", "--others", "--ignored",
               "--exclude-standard", "--directory"], timeout=300)
    tracked = tracked_dirs(wt_path)
    candidates = []  # (full_path, tier)
    for rel in out.split("\0"):
        rel = rel.rstrip("/")
        if not rel:
            continue
        name = os.path.basename(rel)
        if name in BUILD_NAMES or name.endswith(BUILD_SUFFIXES):
            tier = "A"
        elif name in DEP_NAMES:
            tier = "B"
        else:
            continue
        # Reason: `--directory` only lists fully ignored dirs, but a stale .gitignore can
        # still leave tracked files inside; such a path must never be reported as deletable.
        if rel in tracked:
            continue
        candidates.append((os.path.join(wt_path, rel), tier))
    sizes = du_many([p for p, _ in candidates])
    meta = {"A": ("构建/测试产物", "删，构建时重建"), "B": ("依赖目录", "删后需重装依赖")}
    rows = [Row(path, sizes.get(path, 0), meta[tier][0], tier, "gitignore 命中，无 tracked 文件", meta[tier][1],
                command=rm_command(path)) for path, tier in candidates]
    return fold_small(rows, min_kib, wt_path)


def mentions(project_name, name):
    """True when the project name appears as a whole token, e.g. `pnpm-14555-x` but not `.com.openai` for `co`."""
    if len(project_name) < 3:
        return False
    return re.search(rf"(^|[^a-z0-9]){re.escape(project_name.lower())}([^a-z0-9]|$)", name.lower()) is not None


def temp_rows(project_name, registered, min_kib):
    """Entries under temp roots whose name mentions the project; small ones folded per root."""
    found, seen = [], set()
    for root in TEMP_ROOTS:
        root = os.path.realpath(root) if root else ""
        if not root or root in seen or not os.path.isdir(root):
            continue
        seen.add(root)
        for e in entries(root):
            if mentions(project_name, e.name) and os.path.realpath(e.path) not in registered:
                found.append(e)
    sizes = du_many([e.path for e in found])
    rows = []
    for e in found:
        try:
            days = age_days(e.stat(follow_symlinks=False).st_mtime)
        except OSError:
            continue
        is_dir = e.is_dir(follow_symlinks=False)
        dirty = is_git_dirty(e.path) if is_dir else None
        evidence = f"名字含 `{project_name}`，改动于 {days} 天前"
        if MKTEMP_SUFFIX.search(e.name):
            evidence += "，mktemp 后缀"
        size = sizes.get(e.path, 0)
        if dirty:
            rows.append(Row(e.path, size, "临时目录", "C", evidence + "，git 有未提交改动", "不动"))
        elif days < 1:
            rows.append(Row(e.path, size, "临时目录", "B", evidence, "今天刚动过，确认后删", command=rm_command(e.path)))
        else:
            rows.append(Row(e.path, size, "临时目录", "A", evidence, "删", command=rm_command(e.path)))
    folded = []
    for root in {os.path.dirname(r.path) for r in rows}:
        folded.extend(fold_small([r for r in rows if os.path.dirname(r.path) == root], min_kib, f"{root}/*{project_name}*"))
    return folded


def collect(repo, project_name, min_kib=DEFAULT_MIN_KIB, commands=None):
    repo = os.path.realpath(repo)
    default = default_branch(repo)
    worktrees = list_worktrees(repo)
    commands = running_commands() if commands is None else commands
    rows = worktree_rows(repo, worktrees, default, commands)
    for wt in worktrees:
        if os.path.isdir(wt["path"]):
            rows.extend(artifact_rows(wt["path"], min_kib))
    registered = {os.path.realpath(w["path"]) for w in worktrees}
    rows.extend(temp_rows(project_name, registered, min_kib))
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("repo", help="path inside a git repository")
    ap.add_argument("--name", help="project name used to match temp dirs (default: repo dir name)")
    ap.add_argument("--min-mib", type=int, default=20, help="fold rows smaller than this (default 20)")
    ap.add_argument("--json", action="store_true", help="emit JSON rows instead of Markdown")
    args = ap.parse_args()

    top = git(["rev-parse", "--show-toplevel"], args.repo).strip()
    if not top:
        sys.exit(f"not a git repository: {args.repo}")
    rows = collect(top, args.name or os.path.basename(top), args.min_mib * 1024)
    if args.json:
        print(json.dumps([r.as_dict() for r in rows], ensure_ascii=False, indent=2))
    else:
        print(render_table(rows, args.min_mib * 1024, f"仓库 `{top}`（只读扫描）"))


if __name__ == "__main__":
    main()
