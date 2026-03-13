# EmailMarketer — 邮件营销自动化平台

一个开箱即用的邮件营销系统，支持联系人管理、模板设计、群发活动、自动化工作流、数据报表，并提供 **MCP Server** 供 AI 助手直接调用。

---

## 目录

- [系统架构](#系统架构)
- [环境要求](#环境要求)
- [安装步骤](#安装步骤)
- [启动服务](#启动服务)
- [MCP Server 接入指南](#mcp-server-接入指南)
- [MCP 工具一览](#mcp-工具一览)
- [工具详细说明](#工具详细说明)
- [配置说明](#配置说明)
- [常见问题](#常见问题)

---

## 系统架构

```
┌─────────────────┐     stdio/SSE      ┌──────────────────┐     HTTP      ┌──────────────────┐
│   AI 助手       │ ◄════════════════► │  MCP Server      │ ◄══════════► │  FastAPI 后端     │
│ (Claude/Cursor) │                    │  (run_mcp.py)    │              │  (run_api.py)     │
└─────────────────┘                    │  端口: 8101(SSE) │              │  端口: 8100       │
                                       └──────────────────┘              └────────┬─────────┘
                                                                                  │
                                                                         ┌────────▼─────────┐
                                                                         │  SQLite 数据库    │
                                                                         │  data/emailmarketer.db
                                                                         └──────────────────┘
```

- **FastAPI 后端**（端口 8100）：核心业务逻辑、SMTP 发送、工作流引擎
- **MCP Server**：封装后端 API，通过 stdio 或 SSE 协议暴露给 AI 助手
- **Next.js 前端**（端口 3000）：Web 管理面板（可选）

---

## 环境要求

- **Python** 3.10+
- **Node.js** 18+（仅前端面板需要）
- **操作系统**：Windows / macOS / Linux

---

## 安装步骤

### 1. 克隆项目

```bash
git clone https://github.com/jhongjun1981/EmailMarketer.git
cd EmailMarketer
```

### 2. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

主要依赖：

| 包名 | 用途 |
|------|------|
| fastapi | Web 框架 |
| uvicorn | ASGI 服务器 |
| sqlalchemy + aiosqlite | 异步 ORM + SQLite |
| aiosmtplib | 异步 SMTP 发送 |
| jinja2 | 邮件模板渲染 |
| mcp[cli] | MCP Server 框架 |
| httpx | HTTP 客户端 |
| apscheduler | 定时任务调度 |
| pyyaml | 配置文件解析 |

### 3. 配置文件

```bash
cp config.example.yaml config.yaml
```

编辑 `config.yaml`，**必须修改**以下项：

```yaml
api:
  api_key: "你的密钥"       # 修改为自定义密钥

smtp:
  default_sender_email: ""   # 可选：默认发件人
  default_sender_name: ""
```

### 4. 安装前端（可选）

```bash
cd web-dashboard
npm install
cd ..
```

---

## 启动服务

### 第一步：启动后端 API（必须）

```bash
python run_api.py
```

默认监听 `0.0.0.0:8100`，可自定义：

```bash
python run_api.py --host 127.0.0.1 --port 9000 --reload
```

启动后会自动：
- 初始化 SQLite 数据库（首次运行自动建表）
- 启动定时调度器（工作流执行、活动检查）
- 开启像素追踪和链接追踪

### 第二步：启动 MCP Server

根据你的 AI 客户端选择传输协议：

**方式 A — stdio（推荐，Claude Desktop / Claude Code 使用）**

不需要手动启动，由 AI 客户端自动拉起（见下方接入配置）。

**方式 B — SSE（Web 客户端 / 远程调用）**

```bash
python run_mcp.py --transport sse --port 8101
```

### 第三步：启动前端面板（可选）

```bash
cd web-dashboard
npm run dev
```

访问 `http://localhost:3000`

---

## MCP Server 接入指南

### Claude Desktop 接入

将以下内容添加到 Claude Desktop 配置文件：

- **Windows**：`%APPDATA%\Claude\claude_desktop_config.json`
- **macOS**：`~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "email-marketer": {
      "command": "python",
      "args": ["你的路径/EmailMarketer/run_mcp.py"],
      "cwd": "你的路径/EmailMarketer",
      "env": {
        "EM_API_URL": "http://localhost:8100",
        "EM_API_KEY": "你的密钥"
      }
    }
  }
}
```

### Claude Code 接入

在项目根目录创建 `.mcp.json`：

```json
{
  "mcpServers": {
    "email-marketer": {
      "command": "python",
      "args": ["你的路径/EmailMarketer/run_mcp.py"],
      "cwd": "你的路径/EmailMarketer",
      "env": {
        "EM_API_URL": "http://localhost:8100",
        "EM_API_KEY": "你的密钥"
      }
    }
  }
}
```

### Cursor 接入

在 Cursor 设置 → MCP Servers 中添加，配置同上。

### SSE 方式接入（通用）

先手动启动 SSE 服务：

```bash
python run_mcp.py --transport sse --port 8101
```

然后在客户端配置 SSE 端点：`http://localhost:8101/sse`

### 环境变量说明

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `EM_API_URL` | `http://localhost:8100` | 后端 API 地址 |
| `EM_API_KEY` | `changeme-your-secret-key` | API 认证密钥 |
| `EM_HTTP_TIMEOUT` | `30` | HTTP 请求超时（秒） |
| `EM_SSE_HOST` | `0.0.0.0` | SSE 绑定地址 |
| `EM_SSE_PORT` | `8101` | SSE 端口 |

---

## MCP 工具一览

接入成功后，AI 助手可使用以下 **7 个工具**：

| 工具名 | 功能 | 典型用途 |
|--------|------|----------|
| `manage_contacts` | 联系人与分段管理 | 添加/导入联系人、创建分段 |
| `manage_templates` | 邮件模板管理 | 创建/预览/测试模板 |
| `manage_campaigns` | 群发活动管理 | 创建活动、发送/定时、查看统计 |
| `manage_workflows` | 自动化工作流 | 新客户欢迎邮件、条件分支 |
| `get_email_reports` | 数据报表 | 全局概览、趋势分析、活跃度排名 |
| `manage_smtp` | SMTP 账户管理 | 添加/测试/删除 SMTP 账户 |
| `send_email` | 快速发送邮件 | 单封邮件发送，支持附件 |

---

## 工具详细说明

### 1. manage_contacts — 联系人管理

**操作（action 参数）：**

| action | 说明 | 必填参数 |
|--------|------|----------|
| `create` | 创建联系人 | email |
| `list` | 列出联系人 | — |
| `get` | 获取详情 | contact_id |
| `update` | 更新联系人 | contact_id |
| `delete` | 删除联系人 | contact_id |
| `import` | 批量导入 | contacts_data |
| `add_to_segment` | 加入分段 | contact_id, segment_id |
| `remove_from_segment` | 移出分段 | contact_id, segment_id |
| `create_segment` | 创建分段 | name |
| `list_segments` | 列出分段 | — |
| `get_segment` | 分段详情 | segment_id |
| `refresh_segment` | 刷新动态分段 | segment_id |
| `segment_contacts` | 分段内联系人 | segment_id |

**可选参数**：name, company, phone, custom_fields, status, search, page, page_size

**示例：**
```
action="import"
contacts_data=[
  {"email": "alice@example.com", "name": "Alice", "company": "Acme"},
  {"email": "bob@example.com", "name": "Bob"}
]
segment_id=1
```

---

### 2. manage_templates — 模板管理

**操作：**

| action | 说明 | 必填参数 |
|--------|------|----------|
| `create` | 创建模板 | name, subject, html_body |
| `list` | 列出模板 | — |
| `get` | 获取详情 | template_id |
| `update` | 更新模板 | template_id |
| `delete` | 删除模板 | template_id |
| `preview` | 渲染预览 | template_id, preview_data |
| `test_send` | 发送测试邮件 | template_id, test_email |

**模板变量（Jinja2）**：`{{name}}`、`{{company}}`、`{{email}}`、`{{unsubscribe_url}}`

**示例：**
```
action="create"
name="欢迎邮件"
subject="欢迎加入，{{name}}！"
html_body="<h1>你好 {{name}}</h1><p>感谢注册。</p>"
```

---

### 3. manage_campaigns — 活动管理

**操作：**

| action | 说明 | 必填参数 |
|--------|------|----------|
| `create` | 创建活动草稿 | name, template_id, sender_email |
| `list` | 列出活动 | — |
| `get` | 活动详情 | campaign_id |
| `send` | 立即发送 | campaign_id |
| `schedule` | 定时发送 | campaign_id, scheduled_at |
| `pause` | 暂停发送 | campaign_id |
| `cancel` | 取消活动 | campaign_id |
| `stats` | 实时统计 | campaign_id |
| `logs` | 发送日志 | campaign_id |

**可选参数**：segment_id, sender_name, reply_to, rate_limit（默认 10 封/秒）

**示例：**
```
action="create"
name="三月促销"
template_id=1
sender_email="marketing@example.com"
segment_id=2
rate_limit=5
```

---

### 4. manage_workflows — 工作流

**操作：**

| action | 说明 | 必填参数 |
|--------|------|----------|
| `create` | 创建工作流 | name, trigger_type |
| `list` | 列出工作流 | — |
| `get` | 详情 | workflow_id |
| `activate` | 激活 | workflow_id |
| `pause` | 暂停 | workflow_id |
| `delete` | 删除 | workflow_id |
| `executions` | 执行日志 | workflow_id |

**触发器类型（trigger_type）：**

| 类型 | 说明 |
|------|------|
| `contact_added` | 新联系人加入分段 |
| `email_opened` | 邮件被打开 |
| `link_clicked` | 链接被点击 |
| `date_field` | 基于日期字段（如注册后 N 天） |
| `manual` | 手动触发 |

**步骤动作类型（steps 数组中的 action_type）：**

| action_type | config 示例 |
|-------------|------------|
| `send_email` | `{"template_id": 2, "sender_email": "hi@example.com"}` |
| `wait` | `{"duration": 72, "unit": "hours"}` |
| `condition` | `{"field": "company", "op": "eq", "value": "X", "true_step": 3, "false_step": 4}` |
| `add_to_segment` | `{"segment_id": 5}` |
| `remove_from_segment` | `{"segment_id": 5}` |
| `update_contact` | `{"fields": {"company": "新公司"}}` |

**示例 — 新客户 3 天后发欢迎邮件：**
```
action="create"
name="新客户欢迎"
trigger_type="contact_added"
trigger_config={"segment_id": 1}
steps=[
  {"action_type": "wait", "config": {"duration": 72, "unit": "hours"}},
  {"action_type": "send_email", "config": {"template_id": 2, "sender_email": "hello@example.com"}}
]
```

---

### 5. get_email_reports — 报表

| report_type | 说明 | 可选参数 |
|-------------|------|----------|
| `overview` | 全局概览（联系人总数、发送量、平均打开/点击率） | — |
| `campaign` | 单活动详细报告 | campaign_id |
| `trends` | 近 N 天趋势（按天聚合） | days（默认 30） |
| `engagement` | 联系人活跃度排名 | limit（默认 20） |

---

### 6. manage_smtp — SMTP 账户

| action | 说明 | 必填参数 |
|--------|------|----------|
| `list` | 列出所有账户 | — |
| `add` | 添加账户 | name, email, password |
| `update` | 修改账户 | account_id |
| `delete` | 删除账户 | account_id |
| `test` | 测试连接 | email, password, to_email |
| `health` | 系统健康检查 | — |

**可选参数**：smtp_host, smtp_port, use_ssl, daily_limit, is_active

---

### 7. send_email — 快速发邮件

| 参数 | 必填 | 说明 |
|------|------|------|
| `to_email` | 是 | 收件人邮箱 |
| `subject` | 是 | 邮件标题 |
| `content` | 否 | 邮件正文 |
| `smtp_account_id` | 否 | SMTP 账户 ID（0 = 自动选择第一个可用） |
| `attachment_path` | 否 | 附件本地绝对路径 |

**示例：**
```
to_email="user@example.com"
subject="测试邮件"
content="<h1>你好</h1><p>这是一封测试邮件。</p>"
smtp_account_id=0
```

---

## 配置说明

### config.yaml 完整参数

```yaml
api:
  host: "0.0.0.0"              # API 监听地址
  port: 8100                    # API 端口
  api_key: "your-secret-key"    # API 认证密钥

mcp:
  sse_host: "0.0.0.0"          # SSE 监听地址
  sse_port: 8101                # SSE 端口
  sse_auth: true                # SSE 是否启用认证

database:
  url: "sqlite+aiosqlite:///data/emailmarketer.db"
  sync_url: "sqlite:///data/emailmarketer.db"

tracking:
  base_url: "http://localhost:8100"  # 追踪链接基础 URL

smtp:
  default_sender_email: ""
  default_sender_name: ""
  default_password: ""

bounce:
  enabled: false                # 退信检测开关
  imap_host: ""
  imap_user: ""
  imap_pass: ""
  check_interval_minutes: 5

scheduler:
  workflow_tick_seconds: 60     # 工作流检查间隔
  campaign_check_seconds: 60   # 活动检查间隔
```

---

## 常见问题

### Q: MCP 工具调用报错 "连接失败"

后端 API 未启动。请先运行：
```bash
python run_api.py
```

### Q: 如何验证 API 是否正常？

```bash
curl -H "X-API-Key: your-key" http://localhost:8100/api/v1/system/health
```

### Q: 修改代码后需要做什么？

重启对应服务：
- 修改了 `api/` 或 `core/` 下的文件 → 重启 `python run_api.py`
- 修改了 `mcp_server/` 下的文件 → 重启 MCP Server

### Q: 如何添加第一个 SMTP 账户？

通过 MCP 工具：
```
manage_smtp(action="add", name="我的邮箱", email="me@example.com", password="密码", smtp_host="smtp.example.com", smtp_port=465, use_ssl=true)
```

或通过 Web 面板：访问 `http://localhost:3000` → 设置页面。

### Q: API 认证如何工作？

所有 API 请求需要在 Header 中携带 `X-API-Key`，值与 `config.yaml` 中的 `api.api_key` 一致。追踪接口（像素/链接）无需认证。

---

## 许可证

MIT License
