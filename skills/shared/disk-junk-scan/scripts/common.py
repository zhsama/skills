"""Shared read-only helpers for disk-junk-scan scripts."""
import os
import re
import subprocess
import time
from dataclasses import asdict, dataclass, field

HOME = os.path.expanduser("~")
# mktemp suffixes: 6-8 alphanumerics after '.' or '-'. A single leading capital
# (".Safari") is a word, not a random token. Require a digit or a second capital.
MKTEMP_SUFFIX = re.compile(
    r"[.-](?=[A-Za-z0-9_]{6,8}$)(?=.*[0-9]|.*[A-Z].*[A-Z])[A-Za-z0-9_]{6,8}$"
)


@dataclass
class Row:
    path: str
    size_kib: int
    category: str
    tier: str  # "A" rebuildable, "B" confirm first, "C" list only
    evidence: str
    action: str
    command: list = field(default_factory=list)  # argv apply.py runs; empty = not automatable
    members: list = field(default_factory=list)  # real paths behind an aggregate row
    member_kib: list = field(default_factory=list)  # sizes parallel to members
    id: int = 0  # 1-based position in the size-sorted table; set by number_rows
    # None: deleting frees size_kib. An int, including 0, is the reclaimable amount
    # when the command does not remove the measured directory.
    reclaim_kib: int | None = None

    def as_dict(self):
        return asdict(self)


def rm_command(*paths):
    return ["rm", "-rf", *paths]


def fold_small(rows, min_kib, label):
    """Fold rm-able rows below min_kib into one aggregate row per (tier, category).

    Keeps the table short for monorepos with hundreds of tiny dirs while still letting
    apply.py remove them in one command. Tier C rows and tool-command rows are untouched.
    """
    keep, groups = [], {}
    for r in rows:
        if r.size_kib >= min_kib or r.tier == "C" or r.command[:2] != ["rm", "-rf"] or r.members:
            keep.append(r)
            continue
        groups.setdefault((r.tier, r.category), []).append(r)
    for (tier, category), items in groups.items():
        paths = [r.path for r in items]
        keep.append(Row(f"{label}/… ({category}, count {len(items)})", sum(r.size_kib for r in items), category, tier,
                        f"Grouped entries, each below {min_kib // 1024} MiB", items[0].action,
                        command=rm_command(*paths), members=paths, member_kib=[r.size_kib for r in items]))
    return keep


def number_rows(rows):
    """Sort by size (desc) and assign table ids so the Markdown table and JSON agree."""
    rows = sorted(rows, key=lambda r: -r.size_kib)
    for i, r in enumerate(rows, 1):
        r.id = i
    return rows


def run(cmd, cwd=None, timeout=120, merge_stderr=False):
    """Run a command and return stdout (optionally with stderr); empty string on any failure."""
    try:
        proc = subprocess.run(
            cmd, cwd=cwd, text=True, timeout=timeout, check=False,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT if merge_stderr else subprocess.PIPE,
        )
        return proc.stdout
    except (OSError, subprocess.TimeoutExpired):
        return ""


def git(args, cwd):
    return run(["git", "-C", str(cwd), *args])


def du_kib(path):
    out = run(["du", "-xsk", str(path)], timeout=900)
    try:
        return int(out.split("\t", 1)[0])
    except (ValueError, IndexError):
        return 0


def du_many(paths, chunk=400):
    """Sizes for many paths with one `du` process per chunk: {path: KiB}.

    Reason: spawning one `du` per path is what dominated the first version's runtime
    (thousands of tiny monorepo dirs); `du` itself is fast on a warm inode cache.
    """
    paths = [str(p) for p in paths]
    sizes = {}
    for i in range(0, len(paths), chunk):
        out = run(["du", "-xsk", *paths[i:i + chunk]], timeout=900)
        for line in out.splitlines():
            kib, _, path = line.partition("\t")
            if kib.isdigit():
                sizes[path] = int(kib)
    return {p: sizes.get(p, 0) for p in paths}


def gib(kib):
    return f"{kib / 1048576:.2f}"


def counted_kib(row):
    """Bytes a row contributes to a tier total. Tool commands may reclaim less than the directory."""
    return row.size_kib if row.reclaim_kib is None else row.reclaim_kib


def parse_reported_free_kib(text):
    """Bytes a tool says it freed or would free. None when the output has no amount.

    Accepts brew ('free approximately 1.2MB'), uv ('(3.1GiB)'), and pnpm ('(123 bytes)').
    """
    if not text:
        return None
    m = re.search(r"free approximately\s+([0-9.]+)\s*([kMGT]?)i?B", text, re.I)
    if m:
        return parse_human_size_kib(f"{m.group(1)}{m.group(2)}B")
    m = re.search(r"\(([0-9.]+)\s*([kMGT])iB\)", text)
    if m:
        mult = {"k": 1024, "M": 1024 ** 2, "G": 1024 ** 3, "T": 1024 ** 4}[m.group(2)]
        return int(float(m.group(1)) * mult / 1024)
    m = re.search(r"\(([0-9.]+)\s*([kMGT])B\)", text)
    if m:
        return parse_human_size_kib(f"{m.group(1)}{m.group(2)}B")
    m = re.search(r"\(([0-9]+)\s+bytes\)", text)
    if m:
        return int(m.group(1)) // 1024
    return None


def depth_breakdown(path, keep=5, min_child_kib=100 * 1024):
    """Largest direct children of a directory, from one `du -d 1`. Empty when none qualify."""
    out = run(["du", "-x", "-d", "1", "-k", path], timeout=900)
    root = os.path.realpath(path)
    children = []
    for line in out.splitlines():
        kib, _, child = line.partition("\t")
        if not kib.isdigit():
            continue
        if os.path.realpath(child.rstrip("/")) == root:
            continue
        size = int(kib)
        if size >= min_child_kib:
            children.append((size, os.path.basename(child.rstrip("/"))))
    children.sort(reverse=True)
    if not children:
        return ""
    return "Largest children include " + ", ".join(f"{name} {gib(size)} GiB" for size, name in children[:keep])


def annotate_breakdown(rows, min_kib=1024 * 1024):
    """Add a depth-1 breakdown to large tier-B directories so drill-down does not walk them again."""
    from concurrent.futures import ThreadPoolExecutor

    chosen = [
        r for r in rows
        if r.tier == "B" and r.size_kib >= min_kib and r.path.startswith("/") and not r.members and os.path.isdir(r.path)
    ]
    if not chosen:
        return rows
    with ThreadPoolExecutor(max_workers=4) as pool:
        notes = list(pool.map(lambda r: depth_breakdown(r.path), chosen))
    for row, note in zip(chosen, notes):
        if note:
            row.evidence += ". " + note
    return rows


def age_days(ts):
    return int((time.time() - ts) / 86400)


def mtime_days(path):
    try:
        return age_days(os.lstat(path).st_mtime)
    except OSError:
        return None


def parse_human_size_kib(text):
    """'3.132GB' / '275.2MB' / '0B' (docker decimal units) -> KiB."""
    m = re.match(r"([\d.]+)\s*([kMGT]?)B", text.strip())
    if not m:
        return 0
    value, unit = float(m.group(1)), m.group(2)
    mult = {"": 1, "k": 1e3, "M": 1e6, "G": 1e9, "T": 1e12}[unit]
    return int(value * mult / 1024)


def entries(path):
    """Direct children of a directory as DirEntry list; empty when unreadable."""
    try:
        return list(os.scandir(path))
    except OSError:
        return []


def is_git_dirty(path):
    """True when a git worktree has uncommitted or untracked changes; None if not a repo."""
    if not os.path.exists(os.path.join(path, ".git")):
        return None
    return bool(git(["status", "--porcelain", "--untracked-files=all"], path).strip())


def command_uses_path(path, command):
    """True when some other process was started with this path in its argv.

    Any binary counts: a browser using a Playwright profile does not mention
    cargo or node. The scanner's own du/grep/scan commands do not count.
    """
    if not path or path not in command:
        return False
    if any(name in command for name in ("apply.py", "scan.py", "scan_repo.py", "scan_machine.py")):
        return False
    argv0 = os.path.basename(command.split(None, 1)[0]) if command.split(None, 1) else ""
    return argv0 not in {"du", "grep", "rg", "find"}


def dedupe(rows):
    """Drop duplicate paths and make nested rows additive.

    * tier A ancestor (whole thing goes, e.g. a removable worktree): its descendants are
      dropped, the ancestor's command already covers them
    * tier B/C ancestor (needs confirmation / stays): kept, but each direct child's
      original size is subtracted once. A grandchild listed on its own is already inside
      that child, so subtracting it again hides bytes the parent `rm -rf` still deletes.
    """
    seen, unique = set(), []
    for r in sorted(rows, key=lambda r: -r.size_kib):
        key = os.path.realpath(r.path)
        if key in seen:
            continue
        if r.members:
            # Reason: two aggregates can claim the same dir (e.g. project names `octane` and
            # `octane-press` both match `octane-press-x`); the first one keeps it.
            kept = [(p, k) for p, k in zip(r.members, r.member_kib) if os.path.realpath(p) not in seen]
            if not kept:
                continue
            r.members, r.member_kib = [p for p, _ in kept], [k for _, k in kept]
            r.size_kib, r.command = sum(r.member_kib), rm_command(*r.members)
            r.path = re.sub(r", count \d+\)$", f", count {len(kept)})", r.path)
            seen.update(os.path.realpath(p) for p in r.members)
        seen.add(key)
        unique.append(r)
    by_path = {os.path.realpath(r.path): r for r in unique}
    paths = list(by_path)
    original = {p: r.size_kib for p, r in by_path.items()}

    def nearest_ancestor(path):
        best = None
        for parent in paths:
            if parent != path and path.startswith(parent + os.sep) and (best is None or len(parent) > len(best)):
                best = parent
        return best

    direct = {}
    for path in paths:
        ancestor = nearest_ancestor(path)
        if ancestor:
            direct.setdefault(ancestor, []).append(by_path[path])
    dropped = set()
    for p, parent in by_path.items():
        descendants = [cp for cp in paths if cp.startswith(p + os.sep)]
        if not descendants:
            continue
        if parent.tier == "A":
            dropped.update(descendants)
        else:
            parent.size_kib = max(original[p] - sum(original[os.path.realpath(c.path)] for c in direct.get(p, [])), 0)
            parent.evidence += " (size excludes separately listed children, but the command removes the whole directory)"
    return [r for r in unique if os.path.realpath(r.path) not in dropped]


def render_table(rows, min_kib, capacity=None):
    """One Markdown table sorted by size, plus tier totals."""
    rows = number_rows(rows)
    shown = [r for r in rows if r.size_kib >= min_kib]
    hidden = [r for r in rows if r.size_kib < min_kib]
    lines = []
    if capacity:
        lines.append(capacity)
        lines.append("")
    lines.append("| # | Path | GiB | Category | Tier | Evidence | Action |")
    lines.append("|---:|---|---:|---|:-:|---|---|")
    for r in shown:
        path = r.path.replace(HOME, "~")
        lines.append(f"| {r.id} | `{path}` | {gib(r.size_kib)} | {r.category} | {r.tier} | {r.evidence} | {r.action} |")
    totals = {}
    partial = any(r.reclaim_kib is not None and r.reclaim_kib != r.size_kib for r in rows)
    for r in rows:
        totals[r.tier] = totals.get(r.tier, 0) + counted_kib(r)
    summary = "  ".join(f"{t}: {gib(totals.get(t, 0))} GiB" for t in ("A", "B", "C"))
    if partial:
        summary += " (totals use reclaimable space)"
    lines.append("")
    lines.append(f"Totals {summary}" + (f" ({len(hidden)} rows below {min_kib // 1024} MiB omitted, totaling {gib(sum(counted_kib(r) for r in hidden))} GiB)" if hidden else ""))
    return "\n".join(lines)
