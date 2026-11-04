#!/usr/bin/env python3
"""Run the machine scan and a repo scan for every git repository under a root,
then print one merged Markdown table. Read-only.

Usage: scan.py [--repos-root DIR] [--depth N] [--min-mib N] [--skip-machine] [--plan FILE] [--json]
"""
import argparse
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scan_machine  # noqa: E402
import scan_repo  # noqa: E402
from common import HOME, annotate_breakdown, dedupe, number_rows, render_table  # noqa: E402

SKIP_DIRS = {"node_modules", "target", ".git", "vendor", ".venv", "Pods"}


def find_repos(root, depth):
    """Main-worktree repositories (a `.git` directory, not file) up to `depth` levels deep."""
    repos = []
    root = os.path.realpath(root)
    for current, dirs, _ in os.walk(root):
        rel_depth = current[len(root):].count(os.sep)
        if os.path.isdir(os.path.join(current, ".git")):
            repos.append(current)
            dirs[:] = []
            continue
        if os.path.exists(os.path.join(current, ".git")):
            dirs[:] = []  # linked worktree: covered by its main repo
            continue
        if rel_depth >= depth:
            dirs[:] = []
            continue
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
    return sorted(repos)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repos-root", default=f"{HOME}/github", help="directory containing git repos (default ~/github)")
    ap.add_argument("--depth", type=int, default=3, help="how deep to look for repos (default 3)")
    ap.add_argument("--min-mib", type=int, default=50, help="fold rows smaller than this (default 50)")
    ap.add_argument("--skip-machine", action="store_true", help="only scan repositories")
    ap.add_argument("--plan", help="write the JSON plan to this path as well as printing the table")
    ap.add_argument("--json", action="store_true", help="print JSON instead of the table")
    args = ap.parse_args()
    min_kib = args.min_mib * 1024

    repos = find_repos(args.repos_root, args.depth) if os.path.isdir(args.repos_root) else []
    commands = scan_repo.running_commands()  # one ps snapshot shared by every repo

    def scan_one(repo):
        print(f"scanning {repo}", file=sys.stderr)
        return scan_repo.collect(repo, os.path.basename(repo), min_kib, commands)

    # Reason: each repo scan mostly waits on git/du; 4 workers keep the SSD busy without thrashing.
    with ThreadPoolExecutor(max_workers=4) as pool:
        machine = pool.submit(lambda: [] if args.skip_machine else scan_machine.collect(min_kib))
        repo_rows = list(pool.map(scan_one, repos))
    rows = machine.result()
    for r in repo_rows:
        rows.extend(r)
    rows = number_rows(annotate_breakdown(dedupe(rows)))
    payload = json.dumps([r.as_dict() for r in rows], ensure_ascii=False, indent=2)
    if args.plan:
        with open(args.plan, "w") as fh:
            fh.write(payload)
            fh.write("\n")
        print(f"plan {args.plan}", file=sys.stderr)
    if args.json:
        print(payload)
        return
    header = scan_machine.capacity_line()
    header += f"  Repositories scanned under `{args.repos_root.replace(HOME, '~')}`: {len(repos)}"
    print(render_table(rows, min_kib, header))


if __name__ == "__main__":
    main()
