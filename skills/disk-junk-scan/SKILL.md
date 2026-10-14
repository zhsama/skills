---
name: disk-junk-scan
description: "扫描 macOS 上与开发/coding agent 相关的可回收磁盘占用：构建与测试产物、包管理与工具缓存、多版本 toolchain、已合并或陈旧的 git worktree、验证/实验用临时目录、agent 工作区、Docker 与 iOS 模拟器数据，以及已卸载应用遗留的孤儿数据。输出一张按大小排序、带风险分级的表。当用户提到磁盘快满、清缓存、找垃圾目录、清理 worktree 或临时验证目录、点名 disk-junk-scan 时使用。默认只读；清理需要用户看过表之后明确授权。"
compatibility: "Requires macOS and Python 3 with the standard library. Cleanup commands are proposed for review and run only after explicit approval."
---

# Disk Junk Scan

## 范围

只看开发者和 coding agent 会产生、且删掉有意义的东西：

- 构建/测试产物、依赖目录（gitignore 命中的）
- 包管理下载缓存、语言 toolchain 多版本
- git worktree（已合并 / 干净未合并 / 有改动）
- `/private/tmp`、`$TMPDIR` 里含工程文件或 mktemp 后缀的目录，测试缓存
- `~/.codex` `~/.claude` `~/.cursor` `~/conductor` 的缓存、日志、备份、worktree
- Docker 可回收项（build cache、未引用镜像/容器/卷）、iOS 模拟器（设备、runtime）、Parallels
- 已卸载应用留下的孤儿数据：`~/Library/{Containers,Application Support,Caches,Group Containers}` 里匹配不到已安装应用的目录

## 不扫、不列

写进脚本或手工下钻时都遵守，避免表里出现不可操作的行、避免为一个数字多等十几秒：

| 不扫什么 | 原因 |
|---|---|
| 微信/QQ/Lark/浏览器/邮件/音乐等个人应用数据，`Documents/Movies/Pictures`，系统目录 | 不是开发产物，再大也不进表；用户点名再看 |
| `~/Library/pnpm/store` 本体 | 上百万硬链接，`du` 要 15 秒；唯一动作 `pnpm store prune` 不需要知道大小 |
| OrbStack `data.img.raw`、在用的 Docker 卷、运行中容器引用的镜像 | 不可手动操作；Docker 可回收量由 `docker system df` 直接给出 |
| agent 会话/配置目录（`~/.codex/sessions`、`~/.cursor/chats` 等） | 不是垃圾，删了就丢历史 |
| 默认 Rust toolchain、`~/.cargo/registry/cache` | 动作是"保留"，列出来没意义 |
| `Saved Application State`、`Preferences`、UUID 命名的容器、`com.apple.*` | KB 级或系统所有 |
| 单个小于阈值的零散产物（monorepo 里几百个 `lib/`、`dist/`、包级 `node_modules`） | 逐个列没用；按 worktree 合并成一行 |
| 全盘 `find -size +1G`、整个 `~` 或 `~/Library` 的 `du` | 分钟级且结论重复；只测固定清单 |

## 流程：plan → 看表 → apply

```
- [ ] 1 scan.py 出表 + 同一份 plan.json（通常几十秒；仓库多或磁盘冷时要几分钟）
- [ ] 2 表里 B 级大项，按 targets.md 下钻，把"这是什么、谁在用"补进依据列
- [ ] 3 把表给用户，先说可用空间和 A 级合计，再说 B 级需要点头的项
- [ ] 4 （仅授权后）apply.py 先 dry-run 给用户看命令，再加 --execute
- [ ] 5 用每行回读的目录差汇报回收。大批删除后立刻读的 `df` 可能少报几十 GiB，隔几分钟再对一次
```

### 1 扫描

```bash
S=~/.agents/skills/disk-junk-scan/scripts
python3 $S/scan.py [--repos-root ~/github] [--min-mib 50]          # 表
python3 $S/scan.py [--repos-root ~/github] --json > /tmp/plan.json  # 同一批行，带命令
```

`scan.py` = 机器级（`scan_machine.py`）+ 对 `--repos-root` 下每个主仓库跑 `scan_repo.py`，并行执行，合并去重后输出。只想看某个仓库：`python3 $S/scan_repo.py <repo>`。

表结构固定：`# | 路径 | GiB | 类别 | 级 | 依据 | 建议`，按大小降序，末尾给 A/B/C 合计。`#` 与 plan.json 里的 `id` 一致，用户说"删 4 和 6"就是 `--rows 4,6`。单个小于 `--min-mib` 的零散目录按 worktree/临时根合并成一行（`…（N 个零散…）`），apply 时一条命令一起删。

### 4 应用

```bash
python3 $S/apply.py /tmp/plan.json --tier A              # dry-run：列出将执行的命令和预计回收
python3 $S/apply.py /tmp/plan.json --tier A --execute    # 执行 A 级
python3 $S/apply.py /tmp/plan.json --rows 4,6 --execute  # 只执行用户点名的行（B 级只能这样）
```

`apply.py` 不做判断，只执行 scan 时记在每行上的 `command`（`rm -rf`、`git worktree remove`、`docker … prune`、`xcrun simctl delete`、`rustup toolchain uninstall`、`npm cache clean` 等），并在每条命令前重新核验：路径还在、没有其他进程的命令行包含该路径、git 目录仍干净、目录下无 tracked 文件；不满足就跳过并写明原因。浏览器、模拟器、headless shell 和 cargo/node 一样算占用。执行时路径更深的行先跑，这样子目录的 `git worktree remove` 发生在父目录的 `rm -rf` 之前。B 级父行的 GiB 已扣除直接子行，但它的命令仍删除整个目录。折叠的 `rm -rf` 按成员逐个删，一个路径失败不影响其余；只读解包目录会 `chmod -R u+w` 后重试，`Operation not permitted` 不重试。C 级和没有命令的行（Parallels、Zed、模型目录等要人工处理的）永远不执行。每行执行后回读目录大小，结束时 `df` 对比。

plan 是扫描那一刻的快照；隔太久再 apply 前重新 scan 一次。

### 2 下钻

脚本给的依据是机械判定，B 级大项要人工补一句归属：孤儿容器对应的应用是不是真卸了、干净未合并的 worktree 对应 PR 状态（`gh pr list --head <branch> --state all`）、`.tmp` 备份里是什么。命令见 [targets.md](targets.md)。看不出归属就写"未知"，不猜。

### 3 分级含义

| 级 | 含义 | 动作 |
|---|---|---|
| A | 可重建，删了只损失重建时间 | 用户说"清 A"即可批量处理 |
| B | 可重建但代价高，或有状态，或判定是启发式的（孤儿数据、未合并 worktree、24 小时内改动过的临时目录） | 逐行让用户点头 |
| C | 有未提交改动或进程在用 | 只报大小，不动 |

判定要点：

- **已合并 worktree**：`git merge-base --is-ancestor <HEAD> <默认分支>` 或上游 `[gone]`。squash merge 识别不到，会落到 B。删 worktree 不删分支。
- **产物**：`git ls-files --others --ignored --directory` 命中，且该目录下没有任何 tracked 文件。
- **孤儿应用数据**：目录名是反向域名（≥3 段），bundle id / 前 3 段前缀 / 签名团队都匹配不到已安装应用，`mdfind` 也找不到。启发式，永远 B。命令行工具（无 .app）的数据目录会被误判，所以要确认。

### 清理规范（apply 之外的手工项也遵守）

- 优先工具自带命令，`rm -rf` 只用于纯产物目录和临时目录。
- `pnpm store prune` 每次清理都顺手跑，不用先量。删 `node_modules` 前按 [targets.md](targets.md) 区分硬链接和独立副本。
- `brew cleanup` 只删过期瓶。表上的 GiB 是整个缓存。`brew cleanup -s` 会连当前瓶一起删，下次安装重新下载。
- 删前再验：`git status --porcelain` 空、`git ls-files -- <path>` 空、`ps -axo command` 里没有这个路径（任何程序，含浏览器）。
- 一行一回读，汇报实测值，不报估算。
- 清完确认在用项目的 `node_modules` 还在，`docker system df` 符合预期。

## 脚本

| 文件 | 作用 |
|---|---|
| `scripts/scan.py` | 入口：机器级 + 全部仓库并行扫，合并成一张表 / plan.json |
| `scripts/apply.py` | 执行 plan 里的命令；默认 dry-run，`--tier A` 或 `--rows`，每行执行前重新核验 |
| `scripts/scan_machine.py` | 机器级：固定开发缓存清单、toolchain、Docker、模拟器、agent 目录、tmp、孤儿应用数据（已安装应用索引缓存在 `~/.cache/disk-junk-scan/`） |
| `scripts/scan_repo.py` | 仓库级：worktree 判定、ignored 产物/依赖、同名临时目录 |
| `scripts/common.py` | 共享：`Row`（含 `command`/`members`/`id`）、批量 `du`、小项折叠、去重、表渲染 |

Python 3 标准库。慢的从来不是 Python，是进程数：第一版每个候选路径各起一个 `du`/`git`，5000 次 spawn 花了 80 秒；现在一个 worktree 一次 `du`、一次 `git ls-files`，加并行。仓库多或磁盘冷时要几分钟。

## 参考

- [targets.md](targets.md) — 各类目录的下钻命令与判定依据
