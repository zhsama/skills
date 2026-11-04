# Personal Agent Skills

供 zhsama 使用的 Agent Skills，按标准 `SKILL.md` 目录分发。

| Skill | 兼容范围与要求 | 用途 |
| --- | --- | --- |
| [ablation-experiment](skills/ablation-experiment/SKILL.md) | 实验方法通用；当前执行版本要求 `gpt-5.6-luna`、`max` 及项目实验工具。 | 主 agent 设计实验与 Luna 分工，用户确认后执行并核对原始证据。 |
| [codex-downgrade](skills/codex-downgrade/SKILL.md) | Codex 数据与服务专用；需要 Python 3.11+ 和本地 Codex 数据。 | 检查 Codex 实际服务的模型是否低于所选模型。 |
| [disk-junk-scan](skills/disk-junk-scan/SKILL.md) | macOS；需要 Python 3 标准库。默认只读，清理须另行授权。 | 扫描可回收的开发与 agent 磁盘占用，并按风险分级。 |
| [issue-brief](skills/issue-brief/SKILL.md) | 通用流程；需要 GitHub 访问、代码阅读和复现能力。 | 按最近发展区挑选进阶开源问题，复现并讲清原理与修复方向。 |
| [issue-review-workflow](skills/issue-review-workflow/SKILL.md) | Requires independent subagents with fresh contexts. | Verify issues, review plans and fixes, and stop for user approval of the findings and repair scope. |
| [ludwig-personal-code-review-preferences](skills/ludwig-personal-code-review-preferences/SKILL.md) | 通用流程；需要目标代码和项目工具链，子代理不可用时可顺序执行。 | 按 Ludwig 偏好审查或等价简化 TypeScript 代码。 |
| [luna-max-subagents](skills/luna-max-subagents/SKILL.md) | 需要支持指定派发参数、`gpt-5.6-luna` 和 `max` 的子代理运行环境。 | 委派 Luna Max 子代理并由主 agent 汇总。未指定数量时默认 3 个，主 agent 也可自行决定。 |
| [sol-max-subagents](skills/sol-max-subagents/SKILL.md) | 需要支持指定派发参数、`gpt-6.1-sol` 和 `max` 的子代理运行环境。 | 委派 Sol Max 子代理并由主 agent 汇总。未指定数量时默认 3 个，主 agent 也可自行决定。 |

“通用”表示流程没有绑定特定模型或平台接口，不表示已经在所有 agent 上完成执行测试。`codex-downgrade` 的检查对象限定为 Codex，运行它的 agent 不必是 GPT。`disk-junk-scan` 的扫描对象限定为 macOS。Luna 与 Sol 技能则要求执行环境实际提供对应模型和子代理能力，仅安装到 Codex 并不能保证满足要求。

## 安装

使用 [skills CLI](https://github.com/vercel-labs/skills)。仓库是私有的，安装者须具备仓库访问权限，并已配置 Git、GitHub CLI 或 SSH 认证；Node.js 版本须满足所用 CLI 版本的要求。

查看可安装的技能：

```sh
npx skills@latest add zhsama/skills --list
```

`--skill` 选择安装内容，`--agent` 选择安装目标。当前 CLI 不根据 skill 的 `compatibility` 字段筛选内容；使用 `--skill '*'` 会选择全部技能。先按上表确认所需能力，再选择安装集合。

### 通用技能

以下示例安装到 Codex；使用其他受支持的 agent 时，将 `codex` 替换为相应名称，例如 `claude-code` 或 `cursor`：

```sh
npx skills@latest add zhsama/skills --global --agent codex \
  --skill issue-brief --skill ludwig-personal-code-review-preferences
```

### Issue review workflow

```sh
npx skills@latest add zhsama/skills --global --agent codex --skill issue-review-workflow
```

### Codex 检查工具

需要访问本地 Codex 会话与配置；在线探测还需要网络和 Codex 的 ChatGPT 登录凭据：

```sh
npx skills@latest add zhsama/skills --global --agent codex --skill codex-downgrade
```

### 磁盘扫描

需要 macOS 和 Python 3。默认只出表；清理命令要在看过表之后另行授权：

```sh
npx skills@latest add zhsama/skills --global --agent codex --skill disk-junk-scan
```

### Luna 执行技能

确认当前子代理运行环境支持 `gpt-5.6-luna`、`max` 及 skill 中列出的派发参数后再安装。两个 skill 相互独立，可以只保留需要的 `--skill` 选项：

```sh
npx skills@latest add zhsama/skills --global --agent codex \
  --skill luna-max-subagents --skill ablation-experiment
```

能力缺失时，Luna 技能会报告限制，不会自动更换模型或让主 agent 代跑。

### Sol 执行技能

确认当前子代理运行环境支持 `gpt-6.1-sol`、`max` 及 skill 中列出的派发参数后再安装。它与 Luna 技能相互独立：

```sh
npx skills@latest add zhsama/skills --global --agent codex --skill sol-max-subagents
```

能力缺失时，Sol 技能会报告限制，不会自动更换模型或让主 agent 代跑。

### 安装范围

不带 `--global` 时安装到当前项目。安装器支持符号链接或复制，使用 `--copy` 可明确选择复制。已有同名 skill 时先比较本地修改，避免覆盖个人改动或产生重复安装。若项目限制只能使用特定包管理器，可在用户目录执行全局安装命令。

如需关闭安装器遥测，可为命令设置 `DO_NOT_TRACK=1`。

## 使用

在 Codex 中输入：

```text
$ablation-experiment 为当前改动准备实验设计和 Luna 子代理方案，先交给我确认
$codex-downgrade 审计最近的 Codex session，看实际服务的模型是不是我选的那个
$disk-junk-scan 扫描可回收的开发磁盘占用，先给表，不要删除任何东西
$issue-brief 依据我的近期贡献选择一个聚焦单一主要能力提升的 issue
$issue-brief https://github.com/owner/repo/issues/123
$issue-review-workflow Verify every issue in <milestone URL>, independently recheck the findings, and bring me the list to confirm.
$ludwig-personal-code-review-preferences 审查当前目标
$luna-max-subagents 分别检查 API 和测试，最后汇总结果
$sol-max-subagents 分别检查 API 和测试，最后汇总结果
```

`issue-brief` 默认止于问题分析和修复建议，需要可用的 GitHub 访问能力。审查 skill 根据任务使用代码、项目工具链和官方资料。安装这些指令不会配置 GitHub 凭证、MCP 服务或项目依赖。

`codex-downgrade` 需要 Python 3.11+，无第三方运行依赖。默认检查本地会话记录，按需使用本地 ChatGPT 登录凭据进行在线探测。

`disk-junk-scan` 需要 macOS 和 Python 3 标准库。它先给出分级表；用户看过表并明确授权后才执行清理。

`ablation-experiment` 可单独安装，无需安装 `luna-max-subagents`。主 agent 会先展示实验设计，以及子代理数量、分工、模型、权限和执行顺序；用户明确同意后才派发实验。执行环境须提供支持 `gpt-5.6-luna` 和 `max` 推理强度的子代理工具；缺少这些能力时会报告限制。每个实验须返回原始调用、变体 diff、日志和数据，由主 agent 验收。

## 更新

```sh
npx skills@latest update ablation-experiment codex-downgrade disk-junk-scan issue-brief issue-review-workflow luna-max-subagents ludwig-personal-code-review-preferences sol-max-subagents
```

## 维护与验证

在 `skills/<skill-name>/` 中维护源文件，保留每个 skill 引用的完整文件。

有特定环境要求时，使用 [Agent Skills 标准的 `compatibility` 字段](https://agentskills.io/specification#compatibility-field)声明。它是兼容要求说明，不会安装模型、授予工具权限或替代运行时检查。通用流程不需要人为添加平台标签。

`agents/openai.yaml` 提供 Codex 的显示名称和默认调用提示，属于可选的平台配置；该文件的存在不决定 skill 正文的兼容范围。兼容性应根据正文和脚本实际依赖的模型、工具、数据及服务判断。

使用 Agent Skills 参考校验器：

```sh
uvx --from skills-ref==0.1.1 agentskills validate skills/ablation-experiment
uvx --from skills-ref==0.1.1 agentskills validate skills/codex-downgrade
uvx --from skills-ref==0.1.1 agentskills validate skills/disk-junk-scan
uvx --from skills-ref==0.1.1 agentskills validate skills/issue-brief
uvx --from skills-ref==0.1.1 agentskills validate skills/issue-review-workflow
uvx --from skills-ref==0.1.1 agentskills validate skills/luna-max-subagents
uvx --from skills-ref==0.1.1 agentskills validate skills/ludwig-personal-code-review-preferences
uvx --from skills-ref==0.1.1 agentskills validate skills/sol-max-subagents
```

GitHub Actions 在推送和拉取请求时执行同样的格式检查。格式检查不代表技能行为经过完整评估。

来源与维护说明见 [PROVENANCE.md](PROVENANCE.md)。
