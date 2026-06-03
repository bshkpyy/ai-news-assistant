# 导入 sys，用来把项目根目录加入 Python 模块搜索路径。
import sys
# 导入 Path，用来计算当前文件所在路径。
from pathlib import Path

# 获取项目根目录，也就是 rag 文件夹的上一级目录。
PROJECT_ROOT = Path(__file__).resolve().parents[1]
# 如果项目根目录还不在模块搜索路径中，就添加进去。
if str(PROJECT_ROOT) not in sys.path:
    # 把项目根目录放到最前面，确保优先导入本项目的 config.py。
    sys.path.insert(0, str(PROJECT_ROOT))

# 导入 OpenAI SDK；DeepSeek 也可以通过 OpenAI 兼容接口调用。
from openai import OpenAI

# 导入模型配置。
from config import (
    # DeepSeek API Key。
    DEEPSEEK_API_KEY,
    # DeepSeek API 地址。
    DEEPSEEK_BASE_URL,
    # 当前模型服务商。
    LLM_PROVIDER,
    # OpenAI API Key。
    OPENAI_API_KEY,
    # OpenAI API 地址。
    OPENAI_BASE_URL,
    # OpenAI 模型名。
    OPENAI_MODEL,
)
# 导入本地 embedding 函数，用来把用户问题变成向量。
from processors.embedder import get_embedding
# 导入相似新闻检索函数，用来从 pgvector 中找相关新闻。
from storage.db import search_similar


# 创建大模型客户端。
def _build_client() -> OpenAI:
    # 如果当前服务商是 OpenAI，就使用 OpenAI 配置。
    if LLM_PROVIDER == "openai":
        # 返回 OpenAI 客户端。
        return OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
    # 默认使用 DeepSeek 客户端。
    return OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)


# 根据当前服务商返回模型名。
def _model_name() -> str:
    # 如果使用 OpenAI，就用 OPENAI_MODEL。
    if LLM_PROVIDER == "openai":
        # 返回 OpenAI 模型名。
        return OPENAI_MODEL
    # 默认使用 DeepSeek 聊天模型。
    return "deepseek-v4-flash"


# 模块加载时创建客户端，后续回答函数复用它。
client = _build_client()


# 定义 RAG 问答函数。
def answer_question(question: str, top_k: int = 3) -> str:
    # 先把用户问题转换成 embedding 向量。
    q_embedding = get_embedding(question)
    # 用问题向量在数据库中检索最相似的历史新闻。
    similar = search_similar(q_embedding, limit=top_k)
    # 如果数据库没有相似新闻，就直接返回提示。
    if not similar:
        # 返回没有上下文的提示。
        return "抱歉，数据库中没有找到相关的历史新闻。"

    # 准备上下文片段列表。
    context_parts = []
    # 遍历数据库返回的相似新闻。
    for row in similar:
        # 拆解每一行查询结果。
        title, url, summary, score, source_time, similarity = row
        # 把新闻信息整理成模型容易阅读的文本块。
        context_parts.append(
            # 标题。
            f"标题：{title}\n"
            # 链接。
            f"链接：{url}\n"
            # 摘要。
            f"摘要：{summary}\n"
            # 新闻分数。
            f"评分：{score}\n"
            # 新闻时间。
            f"时间：{source_time}\n"
            # 向量相似度。
            f"相似度：{similarity:.3f}"
        )
    # 用分隔线把多个新闻上下文拼成一个字符串。
    context = "\n---\n".join(context_parts)

    # 系统提示词，告诉模型只能基于上下文回答。
    system_prompt = (
        # 模型角色。
        "你是一名 AI 行业分析师，请根据提供的新闻上下文回答用户问题。"
        # 如果上下文不足，要诚实说明。
        "如果上下文中没有足够信息，请诚实说明不知道。"
    )
    # 用户消息，把用户问题和相关新闻上下文一起发给模型。
    user_message = f"用户问题：{question}\n\n相关新闻上下文：\n{context}\n\n请基于以上内容给出回答。"

    # 调用聊天接口生成回答。
    response = client.chat.completions.create(
        # 使用当前服务商的模型名。
        model=_model_name(),
        # 提供系统提示词和用户消息。
        messages=[
            # 系统消息。
            {"role": "system", "content": system_prompt},
            # 用户消息。
            {"role": "user", "content": user_message},
        ],
        # 温度低一点，让回答更稳定。
        temperature=0.3,
        # 限制最大回答长度。
        max_tokens=500,
    )
    # 返回模型生成的回答文本。
    return response.choices[0].message.content.strip()


# 只有直接运行 python rag/qa.py 时才进入命令行问答模式。
if __name__ == "__main__":
    # 打印启动提示。
    print("RAG 问答已启动，输入 exit 或 quit 退出。")
    # 进入循环，让用户可以连续提问。
    while True:
        # 从命令行读取用户问题。
        question = input("\n请输入问题：").strip()
        # 如果用户直接回车，就继续等待下一次输入。
        if not question:
            # 跳过本轮循环。
            continue
        # 如果用户输入退出命令，就结束程序。
        if question.lower() in {"exit", "quit", "q"}:
            # 打印退出提示。
            print("已退出 RAG 问答。")
            # 跳出 while 循环。
            break
        # 捕获问答过程中的异常，避免程序直接崩掉。
        try:
            # 调用 RAG 问答函数生成答案。
            answer = answer_question(question)
            # 打印答案。
            print(f"\n回答：{answer}")
        # 捕获异常。
        except Exception as e:
            # 打印错误原因。
            print(f"\n出错：{e}")
