# 导入 LangChain 的 tool 装饰器，用来把普通函数包装成 Agent 工具。
from langchain_core.tools import tool
# 导入 Pydantic，用来定义工具输入参数的结构。
from pydantic import BaseModel, Field

# 导入新闻抓取函数，并改名为 fetch_ai_news_func，避免和工具函数重名。
from fetchers.news import fetch_ai_news as fetch_ai_news_func
# 导入天气获取函数，并改名为 fetch_weather_func。
from fetchers.weather import get_weather as fetch_weather_func


# 定义天气工具的输入参数结构。
class WeatherInput(BaseModel):
    # city 是城市名，例如北京、上海、南昌。
    city: str = Field(description="城市名称，例如：北京、上海、南昌")


# 定义新闻工具的输入参数结构。
class NewsInput(BaseModel):
    # max_items 表示最多获取多少条新闻。
    max_items: int = Field(default=30, description="最多获取多少条 AI 新闻")


# 把 get_weather_tool 包装成 LangChain 工具，并指定输入结构。
@tool(args_schema=WeatherInput)
def get_weather_tool(city: str) -> str:
    # 函数文档会被 Agent 当作工具说明。
    """获取指定城市的实时天气。"""
    # 调用天气模块获取天气字典。
    weather = fetch_weather_func(city)
    # 把天气字典格式化成适合模型阅读的文本。
    return (
        # 城市。
        f"城市：{weather['city']}\n"
        # 天气现象。
        f"天气：{weather['weather']}\n"
        # 温度。
        f"温度：{weather['temperature']}°C\n"
        # 风向。
        f"风向：{weather['winddirection']}\n"
        # 湿度。
        f"湿度：{weather['humidity']}%\n"
        # 更新时间。
        f"更新时间：{weather['reporttime']}"
    )


# 把 get_ai_news_tool 包装成 LangChain 工具。
@tool(args_schema=NewsInput)
def get_ai_news_tool(max_items: int = 30) -> str:
    # 函数文档会被 Agent 当作工具说明。
    """获取国内外 AI 相关新闻。"""
    # 调用新闻抓取函数。
    news = fetch_ai_news_func(max_items)
    # 如果没有新闻，就返回提示文本。
    if not news:
        # 返回没有结果的提示。
        return "没有找到 AI 相关新闻。"

    # 准备一个列表，用来存放每条新闻的文本行。
    lines = []
    # 遍历新闻并从 1 开始编号。
    for i, item in enumerate(news, 1):
        # 读取地区和来源。
        source = f"{item.get('region', '新闻')} / {item.get('source', 'Unknown')}"
        # 拼接一行新闻信息。
        lines.append(f"{i}. [{source}] {item['title']} - {item['url']}")
    # 用换行把所有新闻拼成一段文本。
    return "\n".join(lines)


# 导出工具列表，Agent 创建时会读取这个列表。
tools = [get_weather_tool, get_ai_news_tool]
