# 下钻命令与判定依据

脚本给出候选行之后，用这里的命令把 B/C 级大项的归属查清楚。全部只读。

## 容量口径

```bash
df -h / /System/Volumes/Data      # GiB
df -H /System/Volumes/Data        # GB，接近菜单栏工具口径
diskutil info / | grep -Ei 'Free Space|Purgeable'
tmutil listlocalsnapshots /
```

菜单栏工具按十进制 GB 且计入 purgeable，比 `df -h` 大 7% 以上是正常的。

## git worktree

```bash
git -C <repo> worktree list --porcelain
git -C <wt> status --porcelain --untracked-files=all          # 空 = 干净
git -C <repo> merge-base --is-ancestor <wt-HEAD> main && echo merged
git -C <repo> for-each-ref --format='%(refname:short) %(upstream:track)' refs/heads   # [gone] = 上游已删
gh pr list --repo <owner/repo> --head <branch> --state all    # squash merge 用这个确认
git -C <repo> worktree remove <path>                          # 删（授权后）；目录已丢失用 worktree prune
```

## 构建产物与依赖

```bash
git -C <wt> ls-files -z --others --ignored --exclude-standard --directory | tr '\0' '\n'
git -C <wt> ls-files -- <rel>          # 非空 = 有 tracked 文件，不能删
ps -axo command | grep <path>
```

- Rust `target/` 单仓可到 40 GB+，每个 worktree 各一份。
- 移动端 `android/app/build`、`ios/build`、`ios/Pods`、`.cxx`。
- pnpm 的 `node_modules` 不一定是硬链接。抽几个普通文件看 `st_nlink`：大于 1 时删目录不腾出 store 里的空间；等于 1 是独立副本，`du` 就是实占，删了要重装。两种都跑 `pnpm store prune`。

## 临时目录

```bash
ls -la /private/tmp "$TMPDIR"
stat -f '%Sm %N' -t '%F' /private/tmp/*            # 修改时间
cat <dir>/.git                                     # 是文件且含 gitdir: → 某仓库的 linked worktree
```

- 命名模式：`<项目>-<issue号>-(validation|ablation|perf|bin|cli|tools).<mktemp后缀>`。
- `$TMPDIR` 下 `node-compile-cache` `metro-cache` `v8-compile-cache-*` `tsx-*` `jest_*` `vitest-*` 是测试/编译缓存，A。
- 名字既无工程文件也无 mktemp 后缀的目录不在范围内（可能是别的应用的）。
- `com.apple.*` 不收。反向域名只因最后一段像 mktemp 才命中的，也不收（`com.apple.Safari`、`dev.kdrag0n.MacVirt` 这类）。
- 「24 小时内」按修改时间算，不是自然日。
- 大于 1 GiB 的 B 级目录，依据里的 `构成：` 是 `du -d 1` 的前几名。下钻看这个，不要再量整棵目录。

## agent 目录

| 路径 | 内容 | 级 |
|---|---|---|
| `~/.codex/{cache,tmp,log,shell_snapshots,worktrees}` `~/.cache/codex-runtimes` | 缓存/日志/worktree | A（worktree 看 git 状态） |
| `~/.codex/{sessions,archived_sessions,history.jsonl,*.sqlite}`，以及 `.tmp` 里的 `codex-history-original-backup-*`、`sessions`、`archived_sessions`、`*.sqlite` | 会话历史或它的备份 | C；备份整目录标 B，先看内容。当前 `~/.codex/sessions` 还在时，删的是备份 |
| `~/.claude/{cache,debug}` | 缓存 | A |
| `~/.claude/projects` | 会话 | C |
| `~/.cursor/{worktrees,projects}` | worktree / 会话 | 看 git 状态 / C |
| `~/conductor/workspaces/*` | 每个是一个 clone | 看 git 状态 |

## Docker / OrbStack

```bash
docker system df -v
docker ps -a --size --format 'table {{.Names}}\t{{.Status}}\t{{.Size}}\t{{.Image}}'
docker volume ls; docker volume inspect <vol> --format '{{.Labels}}'      # compose 项目名在 label 里
docker image inspect <img> --format '{{index .Config.Labels "org.opencontainers.image.source"}}'
```

- Build cache → A；未引用镜像/已停容器 → B；未引用卷 → B（可能是历史项目数据库）；运行中容器引用的 → C。
- `~/Library/Group Containers/HUAQ24HBR6.dev.orbstack/data/data.img.raw` 是稀疏镜像，`ls -l` 的 8T 是逻辑大小；不手删，走 prune。

## iOS 模拟器

```bash
xcrun simctl runtime list -j          # sizeBytes、deletable
xcrun simctl list devices -j          # isAvailable=false 的是 runtime 已删的孤儿设备
xcrun simctl delete unavailable       # 只删孤儿设备
xcrun simctl delete <udid>; xcrun simctl runtime delete <identifier>
```

## toolchain 多版本

```bash
rustup toolchain list                 # (default) 标记
fnm list / nvm ls / gvm list / pyenv versions
```

非默认且最近没用的版本 → B。

## 孤儿应用数据

```bash
plutil -extract CFBundleIdentifier raw -o - /Applications/X.app/Contents/Info.plist
codesign -d --verbose=2 /Applications/X.app 2>&1 | grep TeamIdentifier      # 对应 Group Containers 前缀
mdfind "kMDItemCFBundleIdentifier == 'com.foo.bar'"                        # 全盘找 bundle
ls -la ~/Library/Containers/<bundle>/Data                                   # 看里面是什么
```

判定：反向域名命名，且 bundle id / 前 3 段前缀 / 签名团队都匹配不到已安装应用，`mdfind` 也空。Setapp、Homebrew cask 装的 app 都在 `/Applications` 下会被扫到；`~/Applications`、`/System/Applications` 也扫。命令行工具（无 .app）的数据目录会被误判成孤儿，这是它永远 B 的原因。

## 共享存储

| 路径 | 处理 |
|---|---|
| `~/Library/pnpm/store` | 不量大小（`du` 15 秒），直接 `pnpm store prune`；删后确认在用项目的 `node_modules` 还在 |
| `~/Library/Caches/Homebrew` | 表上的 GiB 来自 `brew cleanup -n`。`brew cleanup -s` 连当前瓶一起删，下次安装重新下载 |
| `~/.cache/uv` | `uv cache prune` 没有 dry-run，目录大小不计入合计。收回量以执行时的输出为准 |
| `~/.cargo/registry/src` | 可删，会从 `cache/` 重新解包 |
| `~/.cargo/registry/cache` | 保留，不进表 |
| `~/.cache/uv` | `uv cache prune` |
| `~/go/pkg/mod` | `go clean -modcache` |
