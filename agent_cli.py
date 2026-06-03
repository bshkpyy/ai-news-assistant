# 导入 LangChain Hub，用来拉取现成的 ReAct Prompt 模板。
from langchain import hub
# 导入 AgentExecutor 和 create_react_agent，用来创建 ReAct Agent。
from langchain.agents import AgentExecutor, create_react_agent
# 导入 ChatOpenAI；DeepSeek 兼容 OpenAI Chat 接口，所以也可以用它。
from langchain_openai import ChatOpenAI

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
# 导入日志函数。
from logger import setup_logger
# 导入工具列表。
from tools import tools


# 根据当前服务商生成 LangChain LLM 配置。
def _llm_config() -> dict:
    # 如果当前使用 OpenAI，就返回 OpenAI 配置。
    if LLM_PROVIDER == "openai":
        # 返回 ChatOpenAI 所需参数。
        return {
            # 模型名。
            "model": OPENAI_MODEL,
            # API Key。
            "openai_api_key": OPENAI_API_KEY,
            # API Base URL。
            "openai_api_base": OPENAI_BASE_URL,
        }
    # 默认返回 DeepSeek 配置。
    return {
        # DeepSeek 聊天模型名。
        "model": "deepseek-v4-flash",
        # DeepSeek API Key。
        "openai_api_key": DEEPSEEK_API_KEY,
        # DeepSeek Base URL。
        "openai_api_base": DEEPSEEK_BASE_URL,
    }


# 创建聊天模型对象，temperature=0 表示尽量稳定输出。
llm = ChatOpenAI(**_llm_config(), temperature=0)
# 从 LangChain Hub 拉取 ReAct Prompt 模板。
prompt = hub.pull("hwchase17/react")
# 创建 ReAct Agent，让模型可以选择并调用 tools。
agent = create_react_agent(llm, tools, prompt)
# 创建 AgentExecutor，负责真正运行 Agent。
agent_executor = AgentExecutor(
    # 传入刚创建的 Agent。
    agent=agent,
    # 传入可用工具列表。
    tools=tools,
    # verbose=True 会打印 Agent 思考和调用工具过程。
    verbose=True,
    # 模型输出格式不规范时，尝试自动处理解析错误。
    handle_parsing_errors=True,
    # 限制最多推理 5 轮，避免无限循环。
    max_iterations=5,
)


# 只有直接运行 python agent_cli.py 时才进入命令行助手。
if __name__ == "__main__":
    # 创建 logger。
    logger = setup_logger(__name__)
    # 打印启动提示。
    logger.info("AI assistant started. Type quit or exit to stop.")
    # 进入命令行循环。
    while True:
        # 等待用户输入问题。
        user_input = input("\n你：")
        # 如果用户输入退出命令，就跳出循环。
        if user_input.lower() in ["quit", "exit", "q"]:
            # 退出 while True。
            break
        # 捕获 Agent 执行异常。
        try:
            # 调用 AgentExecutor 处理用户输入。
            result = agent_executor.invoke({"input": user_input})
            # 打印 Agent 的最终回答。
            logger.info(f"Assistant: {result['output']}")
        # 捕获异常。
        except Exception as e:
            # 打印错误原因。
            logger.error(f"Agent error: {e}")
