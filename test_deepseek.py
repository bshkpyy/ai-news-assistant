# 导入 OpenAI SDK；DeepSeek 支持 OpenAI 兼容调用方式。
from openai import OpenAI
# 导入 DeepSeek 的 API Key 和 Base URL。
from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL


# 创建 DeepSeek 客户端。
client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)

# 准备要测试的模型名列表。
models_to_try = [
    # DeepSeek 官方常用聊天模型。
    "deepseek-chat",
    # 你之前测试过的模型名。
    "deepseek-v4-pro",
    # DeepSeek 推理模型。
    "deepseek-reasoner",
    # 当前项目默认使用的模型名。
    "deepseek-v4-flash",
]

# 遍历模型列表，逐个测试是否能正常调用。
for model in models_to_try:
    # 每个模型单独 try，避免一个失败影响其他测试。
    try:
        # 给模型发送一个最简单的 Hi。
        resp = client.chat.completions.create(
            # 当前测试的模型名。
            model=model,
            # 聊天消息列表。
            messages=[{"role": "user", "content": "Hi"}],
            # 限制回复长度，节省 token。
            max_tokens=10,
        )
        # 如果没有报错，就打印模型可用。
        print(f"模型 {model} 可用，回复：{resp.choices[0].message.content}")
    # 捕获模型调用失败。
    except Exception as e:
        # 打印失败原因。
        print(f"模型 {model} 失败：{e}")
