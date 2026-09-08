# Personal Agent Skills

供 zhsama 使用的 Agent Skills，按标准 `SKILL.md` 目录分发。

| Skill | 用途 |
| --- | --- |
| [ablation-experiment](skills/ablation-experiment/SKILL.md) | 主 agent 准备实验设计和 Luna 分工，用户确认后执行消融，由主 agent 核对原始证据。 |
| [codex-downgrade](skills/codex-downgrade/SKILL.md) | 检查 Codex App / CLI 的模型路由与降级情况，支持离线会话检查和在线探测。 |
| [issue-brief](skills/issue-brief/SKILL.md) | 选择适合贡献经验的 issue，尝试复现，解释场景、正常流程、根因和修复方向。 |
| [luna-max-subagents](skills/luna-max-subagents/SKILL.md) | 按 prompt 指定的数量和任务创建 Luna Max 子代理，由主 agent 协调与汇总。 |
| [ludwig-personal-code-review-preferences](skills/ludwig-personal-code-review-preferences/SKILL.md) | 按个人工程偏好审查 TypeScript 生态代码，或在明确要求时保持行为不变地简化代码。 |

## 安装

使用 [skills CLI](https://github.com/vercel-labs/skills)。仓库是私有的，安装者须具备仓库访问权限，并已配置 Git、GitHub CLI 或 SSH 认证。CLI 1.5.23 要求 Node.js 22.20.0 或以上版本。

查看可安装的技能：

```sh
npx skills@latest add zhsama/skills --list
```

交互选择并安装到个人 Codex 环境：

```sh
npx skills@latest add zhsama/skills --global --agent codex
```

只安装一个：

```sh
npx skills@latest add zhsama/skills --skill issue-brief --global --agent codex
```

安装全部：

```sh
npx skills@latest add zhsama/skills --skill '*' --global --agent codex
```

不带 `--global` 时安装到当前项目。安装器支持符号链接或复制，使用 `--copy` 可明确选择复制。已有同名 skill 时先比较本地修改，避免覆盖个人改动或产生重复安装。若项目限制只能使用特定包管理器，可在用户目录执行全局安装命令。

如需关闭安装器遥测，可为命令设置 `DO_NOT_TRACK=1`。

## 使用

在 Codex 中输入：

```text
$ablation-experiment 为当前改动准备实验设计和 Luna 子代理方案，先交给我确认
$codex-downgrade 检查当前任务是否有模型降级证据
$issue-brief
$issue-brief https://github.com/owner/repo/issues/123
$luna-max-subagents 创建 2 个子代理，分别检查 API 和测试，最后汇总结果
$ludwig-personal-code-review-preferences 审查当前修改
```

`issue-brief` 默认止于问题分析和修复建议，需要可用的 GitHub 访问能力。审查 skill 根据任务使用代码、项目工具链和官方资料。安装这些指令不会配置 GitHub 凭证、MCP 服务或项目依赖。

`codex-downgrade` 需要 Python 3.11+，无第三方运行依赖。默认检查本地会话记录，按需使用本地 ChatGPT 登录凭据进行在线探测。

`ablation-experiment` 可单独安装，无需安装 `luna-max-subagents`。主 agent 会先展示实验设计，以及子代理数量、分工、模型、权限和执行顺序；用户明确同意后才派发实验。执行环境须提供支持 `gpt-5.6-luna` 和 `max` 推理强度的子代理工具；缺少这些能力时会报告限制。每个实验须返回原始调用、变体 diff、日志和数据，由主 agent 验收。

```sh
npx skills@latest add zhsama/skills --skill ablation-experiment --global --agent codex
```

## 更新

```sh
npx skills@latest update ablation-experiment codex-downgrade issue-brief luna-max-subagents ludwig-personal-code-review-preferences
```

## 维护与验证

在 `skills/` 中维护源文件，保留每个 skill 引用的完整文件。`agents/openai.yaml` 提供 Codex 的显示名称和默认调用提示。

使用 Agent Skills 参考校验器：

```sh
uvx --from skills-ref==0.1.1 agentskills validate skills/ablation-experiment
uvx --from skills-ref==0.1.1 agentskills validate skills/codex-downgrade
uvx --from skills-ref==0.1.1 agentskills validate skills/issue-brief
uvx --from skills-ref==0.1.1 agentskills validate skills/luna-max-subagents
uvx --from skills-ref==0.1.1 agentskills validate skills/ludwig-personal-code-review-preferences
```

GitHub Actions 在推送和拉取请求时执行同样的格式检查。格式检查不代表技能行为经过完整评估。

来源与维护说明见 [PROVENANCE.md](PROVENANCE.md)。
