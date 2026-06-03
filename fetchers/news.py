# 导入 time，用于生成兜底时间戳和控制 HN 请求间隔。
import time
# 导入 XML 解析库，用于解析 RSS Feed。
import xml.etree.ElementTree as ET
# 导入 RSS 日期解析函数，用于解析 pubDate。
from email.utils import parsedate_to_datetime
# 导入 HTML 实体还原函数，例如把 &amp; 还原成 &。
from html import unescape

# 导入 requests，用于发送网络请求。
import requests


# 单个请求最多等待 5 秒，避免程序卡在某个新闻源。
REQUEST_TIMEOUT = 5
# Hacker News 最多扫描 40 条热门新闻，避免逐条请求太慢。
HN_SCAN_LIMIT = 40

# AI 相关关键词；标题或描述命中这些词，就认为是 AI 新闻。
AI_KEYWORDS = [
    # OpenAI 和 GPT 相关关键词。
    "openai", "gpt", "chatgpt",
    # 大语言模型相关关键词。
    "llm", "large language model", "language model",
    # Agent 和工具调用相关关键词。
    "langchain", "mcp", "model context protocol", "ai agent",
    # 国外常见模型和公司。
    "claude", "anthropic", "gemini", "llama", "mistral", "deepmind",
    # 技术主题关键词。
    "transformer", "vector database", "rag", "embedding",
    # 训练和生成式 AI 关键词。
    "fine-tuning", "prompt engineering", "diffusion",
    # 国内外常见模型名。
    "deepseek", "moonshot", "kimi",
    # 中文 AI 关键词。
    "人工智能", "大模型", "生成式ai", "生成式 ai", "智能体", "多模态",
    # 中文技术关键词。
    "深度学习", "机器学习", "自然语言", "模型训练", "推理模型",
    # 中文 RAG/向量相关关键词。
    "向量数据库", "检索增强",
    # AI 应用和硬件相关关键词。
    "机器人", "自动驾驶", "算力", "芯片", "英伟达",
    # 国内常见 AI 公司和模型。
    "智谱", "月之暗面", "通义", "千问", "豆包", "文心",
    # 国内其他模型厂商。
    "讯飞星火", "阶跃星辰", "百川智能", "面壁智能",
]

# 国内 RSS 源列表，每个元素是“来源名称 + RSS 地址”。
DOMESTIC_RSS_FEEDS = [
    # 36氪综合 RSS，后面会通过关键词筛选 AI 新闻。
    ("36Kr", "https://36kr.com/feed"),
]

# 国外 RSS 源列表，每个元素是“来源名称 + RSS 地址”。
FOREIGN_RSS_FEEDS = [
    # OpenAI 官方新闻 RSS。
    ("OpenAI News", "https://openai.com/news/rss.xml"),
    # TechCrunch AI 分类 RSS。
    ("TechCrunch AI", "https://techcrunch.com/category/artificial-intelligence/feed/"),
]


# 判断一段文本是否包含 AI 关键词。
def is_ai_related_text(text: str) -> bool:
    # 空文本直接判定为不相关。
    if not text:
        # 返回 False 表示不是 AI 新闻。
        return False
    # 英文统一转小写，方便大小写不敏感匹配。
    text_lower = text.lower()
    # 只要任意关键词出现在文本中，就返回 True。
    return any(keyword in text_lower for keyword in AI_KEYWORDS)


# 获取 Hacker News 热门新闻 ID。
def fetch_top_stories_ids(limit=100):
    # HN 官方 Firebase 热门新闻接口。
    url = "https://hacker-news.firebaseio.com/v0/topstories.json"
    # 发送请求并设置超时。
    resp = requests.get(url, timeout=REQUEST_TIMEOUT)
    # 如果 HTTP 状态码不是成功，就抛出异常。
    resp.raise_for_status()
    # 返回前 limit 个新闻 ID。
    return resp.json()[:limit]


# 根据 HN item ID 获取单条新闻详情。
def fetch_item(item_id):
    # HN 单条 item 接口。
    url = f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json"
    # 请求单条新闻详情。
    resp = requests.get(url, timeout=REQUEST_TIMEOUT)
    # 请求失败时抛出异常。
    resp.raise_for_status()
    # 返回解析后的 JSON 字典。
    return resp.json()


# 从 Hacker News 热门新闻中筛选 AI 新闻。
def fetch_hn_ai_news(max_items=100, sleep=0.05):
    # 先拿到热门新闻 ID 列表。
    story_ids = fetch_top_stories_ids(max_items)
    # 准备用来保存筛选结果的列表。
    ai_news = []
    # 遍历每个新闻 ID。
    for sid in story_ids:
        # 获取新闻详情。
        item = fetch_item(sid)
        # 安全读取标题；item 为空时给空字符串。
        title = item.get("title", "") if item else ""
        # 只保留类型为 story 且标题包含 AI 关键词的新闻。
        if item and item.get("type") == "story" and is_ai_related_text(title):
            # 把 HN 字段转换成项目统一字段。
            ai_news.append({
                # 给 HN 新闻 ID 加前缀，避免和其他源冲突。
                "id": f"hn-{item['id']}",
                # 新闻标题。
                "title": title,
                # 新闻链接；如果没有外链，就用 HN 讨论页。
                "url": item.get("url", f"https://news.ycombinator.com/item?id={item['id']}"),
                # HN 分数。
                "score": item.get("score", 0),
                # HN 作者名。
                "by": item.get("by", "Hacker News"),
                # HN 发布时间戳。
                "time": item.get("time", int(time.time())),
                # 来源名称。
                "source": "Hacker News",
                # 地区标签。
                "region": "国外",
            })
        # 每次请求后暂停一小会儿，避免请求过快。
        time.sleep(sleep)
    # 返回 HN AI 新闻列表。
    return ai_news


# 从 XML 节点中读取指定标签文本。
def _node_text(node, tag: str) -> str:
    # 查找子标签。
    child = node.find(tag)
    # 如果标签不存在或文本为空，就返回空字符串。
    if child is None or child.text is None:
        # 返回空字符串。
        return ""
    # 去掉首尾空白，并还原 HTML 实体。
    return unescape(child.text.strip())


# 把 RSS 时间字符串转成 Unix 时间戳。
def _parse_rss_time(value: str) -> int:
    # 如果没有时间，就用当前时间兜底。
    if not value:
        # 返回当前时间戳。
        return int(time.time())
    # 尝试解析 RSS 时间。
    try:
        # parsedate_to_datetime 可以解析 RSS 常见日期格式。
        return int(parsedate_to_datetime(value).timestamp())
    # 如果解析失败，就使用当前时间。
    except Exception:
        # 返回当前时间戳。
        return int(time.time())


# 从单个 RSS 源抓取新闻。
def fetch_rss_ai_news(source: str, url: str, region: str, max_items=50, filter_ai=True):
    # 请求 RSS XML。
    resp = requests.get(url, timeout=REQUEST_TIMEOUT, headers={"User-Agent": "ai-news-assistant/1.0"})
    # 请求失败时抛出异常。
    resp.raise_for_status()
    # 把 XML 字符串解析成 XML 树。
    root = ET.fromstring(resp.content)
    # 取前 max_items 个 item。
    items = root.findall(".//item")[:max_items]
    # 准备新闻列表。
    news = []
    # 遍历 RSS item。
    for index, item in enumerate(items):
        # 读取标题。
        title = _node_text(item, "title")
        # 读取链接。
        link = _node_text(item, "link")
        # 读取描述。
        description = _node_text(item, "description")
        # 如果需要 AI 关键词过滤，但标题和描述都没命中，就跳过。
        if filter_ai and not is_ai_related_text(f"{title} {description}"):
            # 跳过非 AI 新闻。
            continue
        # 读取发布时间。
        published = _node_text(item, "pubDate")
        # 整理成项目统一新闻格式。
        news.append({
            # 用来源、序号、链接拼出一个相对唯一的 ID。
            "id": f"{source}-{index}-{link or title}",
            # 新闻标题。
            "title": title,
            # 新闻链接。
            "url": link,
            # RSS 通常没有分数，所以设为 0。
            "score": 0,
            # 作者/来源字段。
            "by": source,
            # 发布时间戳。
            "time": _parse_rss_time(published),
            # 来源名称。
            "source": source,
            # 地区标签。
            "region": region,
        })
    # 返回当前 RSS 源的新闻列表。
    return news


# 抓取国内 AI 新闻。
def fetch_domestic_ai_news(max_items=50):
    # 准备结果列表。
    results = []
    # 遍历国内 RSS 源。
    for source, url in DOMESTIC_RSS_FEEDS:
        # 单个源失败不影响整个程序。
        try:
            # 抓取当前国内 RSS 源，并做 AI 关键词过滤。
            results.extend(fetch_rss_ai_news(source, url, "国内", max_items=max_items))
        # 捕获当前源失败。
        except Exception as e:
            # 打印失败原因，方便调试。
            print(f"国内新闻源获取失败: {source} - {e}")
    # 返回国内新闻。
    return results


# 抓取国外 AI 新闻。
def fetch_foreign_ai_news(max_items=100, sleep=0.05):
    # 准备结果列表。
    results = []
    # HN 容易因为网络慢超时，所以单独捕获。
    try:
        # 抓取 HN AI 新闻。
        results.extend(fetch_hn_ai_news(max_items=max_items, sleep=sleep))
    # 捕获 HN 失败。
    except Exception as e:
        # 打印失败原因，后续 RSS 仍然继续。
        print(f"Hacker News 获取失败: {e}")
    # 遍历国外 RSS 源。
    for source, url in FOREIGN_RSS_FEEDS:
        # 单个源失败不影响其他源。
        try:
            # 这些 RSS 本身就是 AI 相关源，所以不再用关键词过滤。
            results.extend(fetch_rss_ai_news(source, url, "国外", max_items=20, filter_ai=False))
        # 捕获当前 RSS 源失败。
        except Exception as e:
            # 打印失败原因。
            print(f"国外新闻源获取失败: {source} - {e}")
    # 返回国外新闻。
    return results


# 按 URL 或标题去重。
def _dedupe(news_items):
    # seen 保存已经出现过的 key。
    seen = set()
    # deduped 保存去重后的新闻。
    deduped = []
    # 遍历新闻列表。
    for item in news_items:
        # 优先用 URL 去重；没有 URL 时用标题。
        key = (item.get("url") or item.get("title") or "").strip().lower()
        # 如果 key 为空或已经出现过，就跳过。
        if not key or key in seen:
            # 跳过当前重复项。
            continue
        # 记录当前 key。
        seen.add(key)
        # 保存当前新闻。
        deduped.append(item)
    # 返回去重结果。
    return deduped


# 把国内和国外新闻交替混合。
def _mix_regions(domestic_news, foreign_news):
    # mixed 保存最终混合结果。
    mixed = []
    # 取两个列表中更长的长度。
    max_len = max(len(domestic_news), len(foreign_news))
    # 按下标交替取新闻。
    for index in range(max_len):
        # 如果当前下标有国内新闻，就加入结果。
        if index < len(domestic_news):
            # 添加国内新闻。
            mixed.append(domestic_news[index])
        # 如果当前下标有国外新闻，就加入结果。
        if index < len(foreign_news):
            # 添加国外新闻。
            mixed.append(foreign_news[index])
    # 返回混合后的新闻。
    return mixed


# 项目主入口：抓取国内外 AI 新闻。
def fetch_ai_news(max_items=100, sleep=0.05):
    # HN 扫描数量至少等于 max_items，但不超过 HN_SCAN_LIMIT。
    scan_count = min(max(max_items, HN_SCAN_LIMIT), HN_SCAN_LIMIT)
    # 抓取国外新闻。
    foreign_news = fetch_foreign_ai_news(max_items=scan_count, sleep=sleep)
    # 抓取国内新闻；国内 RSS 多取一些，过滤后更容易有结果。
    domestic_news = fetch_domestic_ai_news(max_items=max(50, max_items))
    # 国内新闻按发布时间倒序。
    domestic_news = sorted(domestic_news, key=lambda item: item.get("time", 0), reverse=True)
    # 国外新闻按发布时间倒序。
    foreign_news = sorted(foreign_news, key=lambda item: item.get("time", 0), reverse=True)
    # 国内外交替混合后去重。
    mixed_news = _dedupe(_mix_regions(domestic_news, foreign_news))
    # 最多返回 max_items 条；邮件数量就是这里控制的。
    return mixed_news[:max_items]


# 只有直接运行 python fetchers/news.py 时才执行测试。
if __name__ == "__main__":
    # 抓取最多 50 条做测试。
    news = fetch_ai_news(50)
    # 打印新闻总数。
    print(f"找到 {len(news)} 条 AI 新闻：")
    # 只打印前 20 条，避免终端太长。
    for item in news[:20]:
        # 打印地区、来源和标题。
        print(f"[{item['region']}/{item['source']}] {item['title']}")
