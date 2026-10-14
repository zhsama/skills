#!/usr/bin/env python3
"""Apply a disk-junk-scan plan: run the per-row cleanup commands recorded by scan.py --json.

Dry-run by default. Rules that cannot be bypassed:
  * tier C rows and rows without a command are never executed
  * tier B rows run only when selected explicitly with --rows
  * every row is re-verified right before its command runs (path still exists, no tracked
    files, no running process inside, git worktree still clean)

Usage:
  scan.py --json > /tmp/plan.json
  apply.py /tmp/plan.json --tier A              # dry run: show what would run
  apply.py /tmp/plan.json --tier A --execute    # do it
  apply.py /tmp/plan.json --rows 4,6,13 --execute
"""
import argparse
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import HOME, du_many, gib, git, is_git_dirty, run  # noqa: E402

PROCESS_HINTS = ("cargo", "rustc", "rust-analyzer", "jest", "vitest", "node", "pnpm", "tsc", "python", "gradle", "xcodebuild")


def avail_kib():
    out = run(["df", "-k", "/System/Volumes/Data"]).splitlines()
    return int(out[1].split()[3]) if len(out) > 1 else 0


def real_paths(row):
    """Filesystem paths a row's command will touch (none for docker:// and simctl:// rows)."""
    if row["members"]:
        return row["members"]
    return [row["path"]] if row["path"].startswith("/") else []


def verify(row, commands):
    """Return a reason to skip, or None when the row is still safe to act on."""
    paths = [p for p in real_paths(row) if os.path.lexists(p)]
    if real_paths(row) and not paths:
        # `git worktree prune` exists precisely because the directory is gone.
        return None if "prune" in row["command"] else "路径已不存在"
    for p in paths:
        if any(p in c and any(h in c for h in PROCESS_HINTS) for c in commands):
            return f"有进程在用 {p}"
        top = git(["rev-parse", "--show-toplevel"], p if os.path.isdir(p) else os.path.dirname(p)).strip()
        if not top:
            continue
        if os.path.realpath(top) == os.path.realpath(p):
            # Reason: the target is a whole worktree; only a clean one may go.
            if is_git_dirty(p):
                return f"worktree 有未提交改动 {p}"
        elif git(["ls-files", "--", os.path.relpath(p, top)], top).strip():
            return f"含 tracked 文件 {p}"
    return None


def select(rows, tier, ids):
    chosen = []
    for r in rows:
        if ids and r["id"] in ids:
            chosen.append(r)
        elif tier and not ids and r["tier"] == tier:
            chosen.append(r)
    return chosen


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("plan", help="JSON produced by scan.py --json")
    ap.add_argument("--tier", choices=["A"], help="run every tier A row (B needs --rows)")
    ap.add_argument("--rows", help="comma-separated table ids to run, e.g. 4,6,13")
    ap.add_argument("--execute", action="store_true", help="actually run; default is dry run")
    args = ap.parse_args()
    if not args.tier and not args.rows:
        ap.error("choose --tier A or --rows N,M,...")

    with open(args.plan) as fh:
        rows = json.load(fh)
    ids = {int(x) for x in args.rows.split(",")} if args.rows else set()
    chosen = select(rows, args.tier, ids)
    commands = [line.strip() for line in run(["ps", "-axo", "command="]).splitlines() if "apply.py" not in line]

    before = avail_kib()
    mode = "EXECUTE" if args.execute else "DRY RUN"
    print(f"[{mode}] 可用 {gib(before)} GiB，候选 {len(chosen)} 行\n")
    print("| # | 路径 | GiB | 级 | 命令 | 结果 |")
    print("|---:|---|---:|:-:|---|---|")
    freed_est = 0
    for r in chosen:
        path = r["path"].replace(HOME, "~")
        cmd = " ".join(r["command"]) if r["command"] else ""
        cmd_short = (cmd[:80] + "…") if len(cmd) > 80 else cmd
        if r["tier"] == "C" or not r["command"]:
            print(f"| {r['id']} | `{path}` | {gib(r['size_kib'])} | {r['tier']} | | 跳过：不可自动处理 |")
            continue
        if r["tier"] == "B" and r["id"] not in ids:
            print(f"| {r['id']} | `{path}` | {gib(r['size_kib'])} | B | | 跳过：B 级需用 --rows 点名 |")
            continue
        reason = verify(r, commands)
        if reason:
            print(f"| {r['id']} | `{path}` | {gib(r['size_kib'])} | {r['tier']} | `{cmd_short}` | 跳过：{reason} |")
            continue
        if not args.execute:
            print(f"| {r['id']} | `{path}` | {gib(r['size_kib'])} | {r['tier']} | `{cmd_short}` | 将执行 |")
            freed_est += r["size_kib"]
            continue
        size_before = sum(du_many(real_paths(r)).values()) if real_paths(r) else r["size_kib"]
        proc = subprocess.run(r["command"], capture_output=True, text=True, timeout=1800)
        if proc.returncode != 0 and r["command"][:2] == ["rm", "-rf"]:
            # Reason: some tools (dotslash, cargo registry) extract read-only trees; rm cannot
            # unlink inside a dir without u+w. Everything here is user-owned, so restore it and retry.
            subprocess.run(["chmod", "-R", "u+w", *[p for p in real_paths(r) if os.path.lexists(p)]],
                           capture_output=True, timeout=600)
            proc = subprocess.run(r["command"], capture_output=True, text=True, timeout=1800)
        if proc.returncode != 0:
            err = (proc.stderr or proc.stdout).strip().splitlines()
            print(f"| {r['id']} | `{path}` | {gib(r['size_kib'])} | {r['tier']} | `{cmd_short}` | 失败：{err[-1] if err else proc.returncode} |")
            continue
        size_after = sum(du_many(real_paths(r)).values()) if real_paths(r) else 0
        freed_est += max(size_before - size_after, 0)
        print(f"| {r['id']} | `{path}` | {gib(r['size_kib'])} | {r['tier']} | `{cmd_short}` | 完成，回收 {gib(size_before - size_after)} GiB |")

    if args.execute:
        time.sleep(2)  # APFS reports freed space with a short delay
        after = avail_kib()
        print(f"\n可用 {gib(before)} → **{gib(after)} GiB**（df 实测 +{gib(after - before)}；按目录累计 {gib(freed_est)}）")
        print("APFS 可能延迟结算，几分钟后再 `df -h` 一次。")
    else:
        print(f"\n预计回收约 {gib(freed_est)} GiB。加 `--execute` 执行。")


if __name__ == "__main__":
    main()
