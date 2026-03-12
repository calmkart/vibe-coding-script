---
name: fix-review
description: 读取 GitLab MR 的 code review 评论并自动修改代码
argument-hint: "[MR编号]"
disable-model-invocation: true
allowed-tools: Bash, Read, Edit, Write, Grep, Glob, Agent, AskUserQuestion
---

读取 GitLab MR 的所有 code review 评论，分析每条评论的修改建议，然后逐一修改代码。

## 前置一：读取或初始化 GitLab 配置

1. 尝试读取项目 `.claude/gitlab.json` 文件
2. **如果文件不存在、或 token 为空/为占位符 `YOUR_PERSONAL_ACCESS_TOKEN`**，则使用 `AskUserQuestion` 交互式收集配置信息：
   - 问题 1：GitLab 主机名（hostname），提供常见选项如 `gitlab.com`、`gitlab-master.nvidia.com`，并允许用户自定义输入
   - 问题 2：GitLab Personal Access Token，无预设选项，让用户通过 "Other" 自行输入
   - 问题 3：API 协议，选项为 `https`（推荐）和 `http`
   - 问题 4：是否禁用代理（noproxy），选项为 `true`（推荐，添加 `--noproxy '*'`）和 `false`
   - 问题 5：是否跳过 SSL 验证（insecure），选项为 `true`（添加 `-k`）和 `false`（推荐）
3. 收集到信息后，自动创建 `.claude/gitlab.json` 文件写入配置（包含 `noproxy` 和 `insecure` 布尔字段）
4. 如果文件已存在且 token 有效，直接读取使用
5. 构造 API 基础 URL：`{api_protocol}://{hostname}/api/v4`
6. 根据配置构造 curl 额外参数：若 `noproxy` 为 true 则加 `--noproxy '*'`，若 `insecure` 为 true 则加 `-k`。这两个字段不配置时默认为 false

## 前置二：确认 MR 编号

1. 检查 `$ARGUMENTS` 是否包含有效的 MR 编号（纯数字）
2. **如果 `$ARGUMENTS` 为空或不是有效数字**，使用 `AskUserQuestion` 询问用户：
   - 问题：请输入要处理的 MR 编号，无预设选项，让用户通过 "Other" 自行输入数字
3. 将获取到的 MR 编号记为 `{mr_id}` 用于后续步骤

## 步骤

1. 从 git remote 中解析项目路径（如 `calmp/mytool`），URL encode 为 `calmp%2Fmytool`
2. 调用 GitLab API 获取 MR 概况（`{curl_opts}` 为根据配置生成的额外参数，如 `-k --noproxy '*'`）：
   ```
   curl -s {curl_opts} --header "PRIVATE-TOKEN: {token}" "{api_base}/projects/{project_id_encoded}/merge_requests/{mr_id}"
   ```
3. 调用 GitLab API 获取 MR 所有讨论（包含 code review 评论及其关联的文件和行号）：
   ```
   curl -s {curl_opts} --header "PRIVATE-TOKEN: {token}" "{api_base}/projects/{project_id_encoded}/merge_requests/{mr_id}/discussions"
   ```
4. 分析讨论中哪些评论包含代码修改建议（跳过已 resolved 的讨论、纯赞同/确认类评论）
5. 对每条需要修改的评论，根据评论关联的文件路径和行号定位代码，执行修改
6. 完成后汇总所有修改内容
