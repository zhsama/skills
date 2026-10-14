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
    (f"{L}/Developer/Xcode/DerivedData", "Xcode 构建中间", "A", "可重建", "删"),
    (f"{L}/Developer/Xcode/iOS DeviceSupport", "真机符号", "B", "按 iOS 版本一套", "删旧版本"),
    (f"{L}/Developer/Xcode/Archives", "Xcode 归档", "B", "可能含发布包", "确认后删"),
    (f"{L}/Developer/CoreSimulator/Caches", "模拟器缓存", "A", "可重建", "删"),
    (f"{L}/Android/sdk/system-images", "Android 模拟器镜像", "B", "重下代价高", "删不用的 API 级别"),
    (f"{HOME}/.android/avd", "Android 虚拟设备", "B", "设备数据", "删不用的设备"),
    (f"{HOME}/.gradle/caches", "Gradle 缓存", "A", "可重下", "删"),
    (f"{HOME}/.gradle/daemon", "Gradle daemon 日志", "A", "日志", "删"),
    (f"{HOME}/.m2/repository", "Maven 仓库", "B", "重下慢", "确认后删"),
    (f"{HOME}/go/pkg/mod", "Go module 缓存", "B", "重下慢", "`go clean -modcache`"),
    (f"{HOME}/.npm/_cacache", "npm 缓存", "A", "可重下", "`npm cache clean --force`"),
    (f"{HOME}/.yarn/berry/cache", "Yarn 缓存", "A", "可重下", "`yarn cache clean`"),
    (f"{HOME}/.bun/install/cache", "Bun 缓存", "A", "可重下", "`bun pm cache rm`"),
    (f"{L}/Caches/pnpm", "pnpm 下载缓存", "A", "可重下", "删"),
    # ~/Library/pnpm/store is deliberately absent: du over millions of hardlinks costs ~15 s
    # and the only valid action (`pnpm store prune`) does not depend on knowing its size.
    (f"{HOME}/.cargo/registry/src", "Cargo 源码解包", "A", "可从 cache/ 重解", "删"),
    (f"{HOME}/.cargo/git", "Cargo git 依赖", "B", "重 clone", "确认后删"),
    (f"{HOME}/.cache/uv", "uv 缓存", "B", "重下慢", "`uv cache prune`"),
    (f"{HOME}/.cache/pip", "pip 缓存", "A", "可重下", "`pip cache purge`"),
    (f"{HOME}/.cache/huggingface", "HF 模型缓存", "B", "模型重下很慢", "确认后删"),
    (f"{HOME}/.cache/modelscope", "ModelScope 模型缓存", "B", "模型重下很慢", "确认后删"),
    (f"{HOME}/.ollama/models", "Ollama 模型", "B", "模型", "`ollama rm`"),
    (f"{HOME}/.lmstudio", "LM Studio 模型", "B", "模型", "应用内删"),
    (f"{HOME}/.cache/codex-runtimes", "Codex 运行时", "A", "Codex 自动重下", "删"),
    (f"{L}/Caches/ms-playwright", "Playwright 浏览器", "A", "`npx playwright install` 重下", "删"),
    (f"{L}/Caches/Homebrew", "Homebrew 下载", "A", "`brew cleanup` 只删过期瓶，GiB 是整个缓存", "`brew cleanup`"),
    (f"{L}/Caches/CocoaPods", "CocoaPods 缓存", "A", "可重下", "删"),
    (f"{L}/Caches/org.swift.swiftpm", "SwiftPM 缓存", "A", "可重下", "删"),
    (f"{L}/Caches/go-build", "Go 构建缓存", "A", "可重建", "`go clean -cache`"),
    (f"{L}/Caches/node-gyp", "node-gyp 头文件", "A", "可重下", "删"),
    (f"{L}/Caches/typescript", "TS 自动类型获取", "A", "可重下", "删"),
    (f"{L}/Caches/electron", "Electron 二进制", "A", "可重下", "删"),
    (f"{L}/Caches/electron-builder", "electron-builder 缓存", "A", "可重下", "删"),
    (f"{L}/Caches/JetBrains", "JetBrains IDE 缓存", "A", "索引可重建", "删（IDE 需关闭）"),
    (f"{L}/Caches/Codex", "Codex 缓存", "A", "可重建", "删"),
    (f"{L}/Caches/dotslash", "dotslash 缓存", "A", "可重下", "删"),
    (f"{L}/Caches/cursor-compile-cache", "Cursor 编译缓存", "A", "可重建", "删"),
    (f"{L}/Application Support/Code/Cache", "VS Code 缓存", "A", "可重建", "删"),
    (f"{L}/Application Support/Code/CachedData", "VS Code 缓存", "A", "可重建", "删"),
    (f"{L}/Application Support/Cursor/Cache", "Cursor 缓存", "A", "可重建", "删"),
    (f"{L}/Application Support/Cursor/CachedData", "Cursor 缓存", "A", "可重建", "删"),
    (f"{L}/Application Support/Zed", "Zed 数据", "B", "含语言服务器与扩展", "确认后删子目录"),
    (f"{L}/Application Support/JetBrains", "JetBrains 配置/插件", "B", "含插件与索引", "只删旧版本目录"),
    (f"{HOME}/Parallels", "Parallels VM", "B", "整台虚拟机", "在 Parallels 里压缩/迁移"),
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
    (f"{HOME}/.local/share/fnm/node-versions", "Node 版本 (fnm)", ["fnm", "uninstall"]),
    (f"{HOME}/.nvm/versions/node", "Node 版本 (nvm)", None),  # nvm is a shell function
    (f"{HOME}/.gvm/gos", "Go 版本 (gvm)", None),
    (f"{HOME}/.g/versions", "Go 版本 (g)", ["g", "uninstall"]),
    (f"{HOME}/.pyenv/versions", "Python 版本 (pyenv)", ["pyenv", "uninstall", "-f"]),
]
AGENT_ROOTS = [f"{HOME}/.codex", f"{HOME}/.claude", f"{HOME}/.cursor", f"{HOME}/.conductor", f"{HOME}/conductor"]
AGENT_CACHE_NAMES = {"cache", "log", "logs", "shell_snapshots", "debug", "generated_images", "pet-runs"}
AGENT_BACKUP_NAMES = {"tmp", ".tmp", "pet-backups"}
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
            yield (e.path, "Rust toolchain", "B", "非默认 toolchain", "`rustup toolchain uninstall`",
                   ["rustup", "toolchain", "uninstall", e.name])
    for root, cat, cmd in VERSION_MANAGERS:
        for e in entries(root):
            if e.is_dir(follow_symlinks=False):
                yield (e.path, cat, "B", "多版本并存", f"`{cmd[0]} uninstall`" if cmd else "用版本管理器卸载",
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
            rows.append(Row("docker://build-cache", reclaim, "Docker build cache", "A", f"共 {n} 层",
                            "`docker builder prune -af`", command=["docker", "builder", "prune", "-af"]))
        elif kind == "Images":
            rows.append(Row("docker://images-unused", reclaim, "Docker 未引用镜像", "B", f"{n} 张，{active} 张在用",
                            "`docker image prune -a`", command=["docker", "image", "prune", "-af"]))
        elif kind == "Containers":
            rows.append(Row("docker://containers-stopped", reclaim, "Docker 已停止容器", "B", f"{n} 个，{active} 个运行中",
                            "`docker container prune`", command=["docker", "container", "prune", "-f"]))
        elif kind == "Local Volumes":
            rows.append(Row("docker://volumes-unused", reclaim, "Docker 未引用卷", "B", f"{n} 个，{active} 个在用",
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
                        "模拟器 runtime", "B", f"{platform} {rt.get('version')}，{rt.get('state')}",
                        f"`xcrun simctl runtime delete {rt['identifier']}`（无设备使用时）",
                        command=["xcrun", "simctl", "runtime", "delete", rt["identifier"]]))
    devs = [(d, rid) for rid, lst in devices.items() for d in lst if os.path.isdir(d.get("dataPath", ""))]
    sizes = du_many([d["dataPath"] for d, _ in devs])
    for d, rid in devs:
        label = f"{d['name']} / {rid.rsplit('.', 1)[-1]}"
        if d.get("isAvailable", True):
            rows.append(Row(d["dataPath"], sizes[d["dataPath"]], "模拟器设备", "B", f"{label}，{d.get('state')}",
                            "`xcrun simctl delete <udid>`", command=["xcrun", "simctl", "delete", d["udid"]]))
        else:
            rows.append(Row(d["dataPath"], sizes[d["dataPath"]], "模拟器设备（孤儿）", "A", f"{label}，runtime 已不存在",
                            "`xcrun simctl delete unavailable`", command=["xcrun", "simctl", "delete", "unavailable"]))
    return rows


def git_dir_spec(path, category, prefix=""):
    dirty = is_git_dirty(path)
    days = mtime_days(path)
    if dirty:
        return (path, category, "C", f"{prefix}git 有未提交改动，改动于 {days} 天前", "不动")
    if dirty is False:
        return (path, category, "B", f"{prefix}git 干净，改动于 {days} 天前", "确认分支已合并后删")
    return (path, category, "B", f"{prefix}改动于 {days} 天前", "确认后删")


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
                yield (e.path, "agent 缓存/日志", "A", label, "删")
            elif e.name in AGENT_BACKUP_NAMES:
                names = {c.name for c in entries(e.path)}
                session_copy = any(
                    n in {"sessions", "archived_sessions"} or n.startswith("codex-history-original-backup") or n.endswith(".sqlite")
                    for n in names
                )
                note = "，里面有会话备份" if session_copy else "（含历史备份）"
                yield (e.path, "agent 临时/备份", "B", label + note, "看内容后删")


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
        why = ", ".join(w for w, ok in (("含工程文件", dev), ("测试缓存", test_cache), ("mktemp 后缀", mk)) if ok)
        days = mtime_days(e.path)
        if ".git" in names:
            yield git_dir_spec(e.path, "临时目录", why + "；")
        elif days is not None and days < 1:
            yield (e.path, "临时目录", "B", f"{why}，24 小时内改动过", "确认后删")
        else:
            yield (e.path, "临时目录", "A", f"{why}，改动于 {days} 天前", "删")


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
    for root, label in ((f"{L}/Containers", "容器"), (f"{L}/Application Support", "Application Support"), (f"{L}/Caches", "缓存")):
        for e in entries(root):
            n = e.name
            if UUID_NAME.match(n) or not REVERSE_DNS.match(n) or "com.apple." in n or app_known(n, ids):
                continue
            unknown.append((e.path, n, f"{label}，未找到 `{n}` 对应的已安装应用"))
    for e in entries(f"{L}/Group Containers"):
        m = TEAM_PREFIX.match(e.name)
        if not m or "com.apple." in e.name or m.group(0)[:-1] in teams:
            continue
        rest = e.name[len(m.group(0)):]
        rest = rest[6:] if rest.startswith("group.") else rest
        if not app_known(rest, ids):
            unknown.append((e.path, rest, f"Group Container，团队 `{m.group(0)[:-1]}` 无已安装应用"))
    sizes = du_many([p for p, _, _ in unknown])
    rows = []
    for path, bid, evidence in unknown:
        if sizes.get(path, 0) >= min_kib and not app_on_disk(bid):
            rows.append(Row(path, sizes[path], "孤儿应用数据", "B", evidence, "确认应用已卸载后删", command=rm_command(path)))
    return rows


def capacity_line():
    out = run(["df", "-k", "/System/Volumes/Data"]).splitlines()
    if len(out) < 2:
        return ""
    f = out[1].split()
    return f"数据卷 {int(f[1]) / 1048576:.0f} GiB，已用 {f[4]}，可用 **{int(f[3]) / 1048576:.1f} GiB**（只读扫描，未删除）"


def annotate_tool_reclaim(rows):
    """Directory size is not reclaimable when the command only prunes.

    `brew cleanup -n` prints the amount it would free. `uv cache prune` has no
    dry-run, so its directory stays visible but does not enter the tier total.
    """
    for row in rows:
        if row.command == ["brew", "cleanup"] and shutil.which("brew"):
            out = run(["brew", "cleanup", "-n"], timeout=180, merge_stderr=True)
            reclaim = parse_reported_free_kib(out) or 0
            row.evidence += f"（目录 {gib(row.size_kib)} GiB，cleanup 预计收回 {gib(reclaim)} GiB）"
            row.size_kib = reclaim
            row.reclaim_kib = reclaim
        elif row.command[:3] == ["uv", "cache", "prune"]:
            row.evidence += "（prune 不报告预计回收，目录大小不计入合计）"
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
