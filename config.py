# 导入 os，用来读取系统环境变量和 .env 中加载出来的配置。
import os
# 导入 load_dotenv，用来把 .env 文件里的键值对加载到环境变量。
from dotenv import load_dotenv


# 加载当前项目根目录下的 .env 文件。
load_dotenv()

# 读取 DeepSeek API Key，用于调用 DeepSeek 生成摘要。
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
# 读取 DeepSeek API 地址，通常是 https://api.deepseek.com。
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL")
# 读取是否启用 embedding；字符串 true 会转成布尔值 True。
ENABLE_EMBEDDING = os.getenv("ENABLE_EMBEDDING", "false").lower() == "true"

# 读取当前使用的大模型服务商；默认使用 deepseek。
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "deepseek").lower()

# 读取 OpenAI 或中转站的 API Key；如果不用 OpenAI，可以为空。
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# 读取 OpenAI 或中转站的 base URL；默认保留你之前配置的中转地址。
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://shunfen6.win/v1")
# 读取 OpenAI 聊天模型名；只有 LLM_PROVIDER=openai 时才会用到。
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.5")
# 读取 OpenAI 调用方式；responses 表示走 /v1/responses。
OPENAI_WIRE_API = os.getenv("OPENAI_WIRE_API", "responses").lower()
# 读取推理强度配置；只有部分 responses 模型/中转站支持。
OPENAI_REASONING_EFFORT = os.getenv("OPENAI_REASONING_EFFORT", "xhigh")
# 读取是否关闭响应存储；true 表示不让服务端保存响应。
OPENAI_DISABLE_RESPONSE_STORAGE = os.getenv("OPENAI_DISABLE_RESPONSE_STORAGE", "true").lower() == "true"
# 读取远程 embedding 模型名；当前项目已经改成本地 embedding，暂时保留配置。
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
# 读取远程 embedding 维度；当前本地模型固定 384 维，暂时保留配置。
OPENAI_EMBEDDING_DIMENSIONS = int(os.getenv("OPENAI_EMBEDDING_DIMENSIONS", "1536"))

# 读取高德地图 API Key，用于 IP 定位和天气查询。
AMAP_KEY = os.getenv("AMAP_KEY")

# 读取 SMTP 邮件服务器地址，例如 smtp.qq.com。
SMTP_SERVER = os.getenv("SMTP_SERVER")
# 读取 SMTP 端口；如果 .env 没写，就默认使用 587。
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
# 读取发件人邮箱地址。
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
# 读取发件人邮箱授权码或密码。
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
# 读取收件人邮箱地址。
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")

# 读取 PostgreSQL 主机地址。
DB_HOST = os.getenv("DB_HOST")
# 读取 PostgreSQL 端口；默认 5432。
DB_PORT = int(os.getenv("DB_PORT", 5432))
# 读取数据库名称。
DB_NAME = os.getenv("DB_NAME")
# 读取数据库用户名。
DB_USER = os.getenv("DB_USER")
# 读取数据库密码。
DB_PASSWORD = os.getenv("DB_PASSWORD")
