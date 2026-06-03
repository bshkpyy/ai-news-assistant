# 导入 OpenAI SDK；DeepSeek 也兼容 OpenAI SDK 的调用方式。
from openai import OpenAI

# 导入不同模型服务商需要的配置。
from config import (
    # DeepSeek 的 API Key。
    DEEPSEEK_API_KEY,
    # DeepSeek 的 API 地址。
    DEEPSEEK_BASE_URL,
    # 当前选择的大模型服务商，例如 deepseek 或 openai。
    LLM_PROVIDER,
    # OpenAI 或中转站的 API Key。
    OPENAI_API_KEY,
    # OpenAI 或中转站的 API 地址。
    OPENAI_BASE_URL,
    # OpenAI responses 接口是否关闭服务端存储。
    OPENAI_DISABLE_RESPONSE_STORAGE,
    # OpenAI 模型名。
    OPENAI_MODEL,
    # OpenAI reasoning effort 参数。
    OPENAI_REASONING_EFFORT,
    # OpenAI 调用方式，例如 responses。
    OPENAI_WIRE_API,
)


# 创建大模型客户端。
def _build_client() -> OpenAI:
    # 如果配置为 openai，就使用 OpenAI 或中转站配置。
    if LLM_PROVIDER == "openai":
        # 返回 OpenAI 客户端。
        return OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
    # 默认使用 DeepSeek 客户端。
    return OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)


# 根据当前服务商返回模型名。
def _model_name() -> str:
    # 如果使用 OpenAI，就返回 .env 里的 OPENAI_MODEL。
    if LLM_PROVIDER == "openai":
        # 返回 OpenAI 模型名。
        return OPENAI_MODEL
    # 默认返回 DeepSeek 聊天模型。
    return "deepseek-v4-flash"


# 模块加载时创建一个全局 client，后续摘要函数复用它。
client = _build_client()


# 从 Responses API 的返回对象中提取纯文本。
def _extract_response_text(response) -> str:
    # 优先读取 SDK 提供的 output_text 快捷字段。
    text = getattr(response, "output_text", None)
    # 如果 output_text 有内容，就去掉首尾空白后返回。
    if text:
        # 返回纯文本结果。
        return text.strip()

    # 如果没有 output_text，就手动遍历 output 结构。
    chunks = []
    # 遍历响应里的每个 output item。
    for item in getattr(response, "output", []) or []:
        # 遍历 item 里的 content。
        for content in getattr(item, "content", []) or []:
            # 读取 content.text 字段。
            value = getattr(content, "text", None)
            # 如果 text 有内容，就加入 chunks。
            if value:
                # 保存一段文本。
                chunks.append(value)
    # 把所有文本片段合并成最终结果。
    return "\n".join(chunks).strip()


# 定义新闻摘要函数，输入标题和链接，输出中文摘要。
def summarize_news(title: str, url: str = "") -> str:
    # system_prompt 用来告诉模型扮演什么角色、按什么规则输出。
    system_prompt = """你是一名中文科技编辑，擅长将英文或中文科技新闻提炼成简洁中文摘要。
要求：
1. 摘要为一句话，不超过60个汉字。
2. 保留核心技术名词，例如 GPT、LLM、MCP、RAG。
3. 仅根据提供的标题和链接信息提炼。
4. 直接输出摘要文本，不要添加说明或前缀。"""
    # user_message 是传给模型的具体新闻内容。
    user_message = f"新闻标题：{title}\n链接：{url}\n请给出中文摘要。"

    # 如果使用 OpenAI 且配置为 responses，就走 Responses API。
    if LLM_PROVIDER == "openai" and OPENAI_WIRE_API == "responses":
        # 调用 /v1/responses 生成摘要。
        response = client.responses.create(
            # 使用当前配置的模型名。
            model=_model_name(),
            # instructions 相当于系统提示词。
            instructions=system_prompt,
            # input 是用户输入内容。
            input=user_message,
            # 限制输出长度，避免摘要太长。
            max_output_tokens=150,
            # 设置推理强度；部分模型或中转站支持。
            reasoning={"effort": OPENAI_REASONING_EFFORT},
            # 根据配置决定是否让服务端存储响应。
            store=not OPENAI_DISABLE_RESPONSE_STORAGE,
        )
        # 从 Responses API 返回对象中提取文本。
        return _extract_response_text(response)

    # 默认走 Chat Completions，DeepSeek 当前就是这条路径。
    response = client.chat.completions.create(
        # 使用当前服务商的模型。
        model=_model_name(),
        # messages 是聊天上下文列表。
        messages=[
            # 系统消息：告诉模型角色和规则。
            {"role": "system", "content": system_prompt},
            # 用户消息：提供新闻标题和链接。
            {"role": "user", "content": user_message},
        ],
        # 温度越低输出越稳定。
        temperature=0.3,
        # 限制最大输出 token。
        max_tokens=150,
        # 不使用流式输出，直接等待完整结果。
        stream=False,
    )
    # 取出模型回复文本并去掉首尾空白。
    return response.choices[0].message.content.strip()


# 只有直接运行本文件时才执行测试代码。
if __name__ == "__main__":
    # 准备一个测试标题。
    test_title = "Show HN: I built a RAG pipeline with LangChain and pgvector"
    # 打印测试摘要结果。
    print(summarize_news(test_title, "https://example.com"))
