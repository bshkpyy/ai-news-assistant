# AI News Assistant

AI News Assistant 是一个自动化 AI 行业早报项目。它会根据当前公网 IP 获取本地天气，抓取国内外 AI 相关新闻，调用大语言模型生成中文摘要，并通过邮件定时发送 HTML 早报。同时，项目支持使用本地 embedding 模型把新闻摘要写入 PostgreSQL + pgvector，为后续 RAG 问答和语义检索提供基础。

## 功能特性

- 自动天气定位：使用高德地图 IP 定位接口获取当前城市，并查询实时天气。
- 国内外新闻抓取：聚合 36Kr、OpenAI News、TechCrunch AI、Hacker News 等来源。
- AI 新闻过滤：通过中英文关键词筛选 OpenAI、LLM、MCP、RAG、智能体、大模型等相关新闻。
- 中文摘要生成：使用 DeepSeek 或 OpenAI 兼容接口生成简洁中文摘要。
- 邮件自动发送：生成 HTML 格式早报，并通过 SMTP 邮件发送。
- 本地向量化：使用 `sentence-transformers` 本地模型生成 384 维 embedding。能够支持没有embedding能力的api。
- pgvector 存储：将新闻摘要向量写入 PostgreSQL，支持语义相似检索。
- RAG 基础链路：支持基于历史新闻的相似检索和问答。
- 定时任务：默认每天 08:00 自动执行。

## 项目结构

```text
ai-news-assistant/
├── main.py                  # 主程序入口：天气、新闻、摘要、入库、发邮件、定时任务
├── config.py                # 读取 .env 配置
├── logger.py                # 日志配置
├── tools.py                 # LangChain Agent 工具封装
├── agent_cli.py             # ReAct Agent 命令行助手
├── test_deepseek.py         # DeepSeek 连通性测试
├── test_embedding.py        # 本地 embedding 测试
├── requirements.txt         # Python 依赖
├── .env.example             # 环境变量示例，不包含真实密钥
├── fetchers/
│   ├── news.py              # 国内外 AI 新闻抓取
│   └── weather.py           # IP 定位和天气查询
├── processors/
│   ├── summarizer.py        # 大模型新闻摘要
│   └── embedder.py          # 本地 embedding
├── storage/
│   └── db.py                # PostgreSQL + pgvector 存储和检索
├── notifier/
│   └── email_sender.py      # HTML 邮件生成和发送
└── rag/
    └── qa.py                # RAG 问答基础模块
```

## 环境要求

- Python 3.10+
- PostgreSQL
- pgvector 扩展
- 高德地图 Web 服务 API Key
- DeepSeek API Key
- 可用于 SMTP 的邮箱授权码，例如 QQ 邮箱授权码

## 安装步骤

1. 克隆项目：

```bash
git clone <your-repo-url>
cd ai-news-assistant
```

2. 创建虚拟环境：

```bash
python -m venv venv
```

3. 激活虚拟环境：

Windows PowerShell：

```powershell
.\venv\Scripts\activate
```

macOS / Linux：

```bash
source venv/bin/activate
```

4. 安装依赖：

```bash
pip install -r requirements.txt
```

> 第一次运行本地 embedding 时，`sentence-transformers` 会下载模型 `paraphrase-multilingual-MiniLM-L12-v2`。下载完成后会从本地缓存加载。

## 配置环境变量

复制配置模板：

```bash
cp .env.example .env
```

Windows PowerShell：

```powershell
copy .env.example .env
```

然后编辑 `.env`，填写自己的配置。

示例：

```env
# DeepSeek API
DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_BASE_URL=https://api.deepseek.com

# LLM provider: deepseek or openai
LLM_PROVIDER=deepseek

# Local sentence-transformers embedding
ENABLE_EMBEDDING=true

# AMap
AMAP_KEY=your_amap_key

# Email
SMTP_SERVER=smtp.qq.com
SMTP_PORT=587
SENDER_EMAIL=your_email@qq.com
SENDER_PASSWORD=your_email_authorization_code
RECEIVER_EMAIL=receiver@example.com

# PostgreSQL
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ai_news
DB_USER=postgres
DB_PASSWORD=your_database_password
```

不要把 `.env` 上传到 GitHub。`.env` 里包含 API Key、邮箱授权码、数据库密码等敏感信息。

## PostgreSQL 和 pgvector

项目会在启动时自动执行：

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

并创建新闻表：

```sql
CREATE TABLE IF NOT EXISTS news_articles (
    id SERIAL PRIMARY KEY,
    title TEXT,
    url TEXT,
    summary TEXT,
    score INTEGER,
    source_time TIMESTAMP,
    embedding vector(384)
);
```

如果你本地 PostgreSQL 没有安装 pgvector，需要先安装 pgvector 扩展。

## 运行项目

手动运行一次，并启动每天 08:00 的定时任务：

```bash
python main.py
```

程序会依次执行：

1. 初始化数据库
2. 根据 IP 查询当地天气
3. 抓取国内外 AI 新闻
4. 生成中文摘要
5. 生成本地 embedding 并写入 PostgreSQL
6. 发送 HTML 邮件
7. 进入定时任务循环

如果只想测试本地 embedding：

```bash
python test_embedding.py
```

如果只想测试 DeepSeek 连通性：

```bash
python test_deepseek.py
```

## RAG 和 Embedding 说明

项目使用本地模型：

```text
paraphrase-multilingual-MiniLM-L12-v2
```

它会把新闻摘要转换成 384 维向量，并存入 PostgreSQL 的 `embedding vector(384)` 字段。

embedding 的作用是支持语义检索。例如用户问：

```text
最近国内大模型有什么动态？
```

系统可以把问题也转成向量，然后从数据库里找语义最相似的历史新闻，而不是只靠关键词匹配。

RAG 问答入口在：

```bash
python rag/qa.py
```

## GitHub 上传注意事项

建议上传：

- 源码文件
- `requirements.txt`
- `.env.example`
- `README.md`
- `.gitignore`

不要上传：

- `.env`
- `venv/`
- `__pycache__/`
- `app.log`
- 本地模型缓存
- 数据库文件或备份

## 常见问题

### 为什么第一次运行很慢？

第一次运行会下载本地 embedding 模型，下载完成后会缓存到本地，后续启动会快很多。

### 为什么 Hacker News 获取失败？

Hacker News 偶尔会因为网络超时失败。程序会继续使用 36Kr、OpenAI News、TechCrunch AI 等新闻源，不会影响整体流程。

### 为什么不用 DeepSeek 做 embedding？

DeepSeek 当前接口没有提供可用的 embedding 模型。本项目使用本地 `sentence-transformers` 模型完成向量化，不需要额外 API Key。

### 邮件发送失败怎么办？

检查：

- SMTP 服务器是否正确
- SMTP 端口是否正确
- 邮箱是否开启 SMTP 服务
- `SENDER_PASSWORD` 是否是邮箱授权码，而不是登录密码
- 网络是否允许访问 SMTP 服务

## License

This project is for learning and personal research use.
