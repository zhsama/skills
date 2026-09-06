# Personal Agent Skills

供 zhsama 使用的 Agent Skills，按标准 `SKILL.md` 目录分发。

| Skill | 用途 |
| --- | --- |
| [issue-brief](skills/issue-brief/SKILL.md) | 选择适合贡献经验的 issue，尝试复现，解释场景、正常流程、根因和修复方向。 |
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

安装两个：

```sh
npx skills@latest add zhsama/skills --skill '*' --global --agent codex
```

不带 `--global` 时安装到当前项目。安装器支持符号链接或复制，使用 `--copy` 可明确选择复制。已有同名 skill 时先比较本地修改，避免覆盖个人改动或产生重复安装。若项目限制只能使用特定包管理器，可在用户目录执行全局安装命令。

如需关闭安装器遥测，可为命令设置 `DO_NOT_TRACK=1`。

## 使用

在 Codex 中输入：

```text
$issue-brief
$issue-brief https://github.com/owner/repo/issues/123
$ludwig-personal-code-review-preferences 审查当前修改
```

`issue-brief` 默认止于问题分析和修复建议，需要可用的 GitHub 访问能力。审查 skill 根据任务使用代码、项目工具链和官方资料。安装这些指令不会配置 GitHub 凭证、MCP 服务或项目依赖。

## 更新

```sh
npx skills@latest update issue-brief ludwig-personal-code-review-preferences
```

## 维护与验证

在 `skills/` 中维护源文件，保留每个 skill 引用的完整文件。`agents/openai.yaml` 提供 Codex 的显示名称和默认调用提示。

使用 Agent Skills 参考校验器：

```sh
uvx --from skills-ref==0.1.1 agentskills validate skills/issue-brief
uvx --from skills-ref==0.1.1 agentskills validate skills/ludwig-personal-code-review-preferences
```

GitHub Actions 在推送和拉取请求时执行同样的格式检查。格式检查不代表技能行为经过完整评估。

来源与维护说明见 [PROVENANCE.md](PROVENANCE.md)。
