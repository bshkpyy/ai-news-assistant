# 导入日志初始化函数，用来把运行状态打印到控制台和 app.log 文件。
from logger import setup_logger
# 导入天气获取函数；现在不传城市时，会根据当前公网 IP 自动定位。
from fetchers.weather import get_weather
# 导入新闻抓取函数；它会同时抓取国内和国外 AI 新闻。
from fetchers.news import fetch_ai_news
# 导入新闻摘要函数；它会调用 DeepSeek/OpenAI 生成中文摘要。
from processors.summarizer import summarize_news
# 导入本地向量化函数；它会把摘要转成 384 维 embedding。
from processors.embedder import get_embedding
# 导入数据库初始化和新闻入库函数。
from storage.db import init_db, insert_news
# 导入邮件 HTML 生成函数和邮件发送函数。
from notifier.email_sender import create_html_content, send_email
# 导入 embedding 开关；为 true 时才会生成并保存向量。
from config import ENABLE_EMBEDDING
# 导入定时任务库，用来每天固定时间执行任务。
import schedule
# 导入 time，用来让主循环每隔一段时间休眠。
import time
# 导入 datetime，用来把新闻时间戳转成人类可读的时间。
from datetime import datetime


# 创建当前模块使用的 logger，名字叫 main。
logger = setup_logger("main")


# 定义每日早报任务；手动运行和定时运行都会调用这个函数。
def job():
    # 记录任务开始，方便你在终端和日志文件里确认程序启动了。
    logger.info("开始执行每日任务...")
    # 用 try 包住整个任务，避免一个异常直接让程序崩掉。
    try:
        # 初始化数据库表和 pgvector 扩展；如果已经存在，不会重复创建。
        init_db()
        # 根据当前 IP 自动定位城市，并获取实时天气。
        weather = get_weather()
        # 把天气结果写入日志，方便确认定位是否正确。
        logger.info(f"天气获取成功: {weather['city']} {weather['weather']} {weather['temperature']}°C")
        # 记录开始抓取新闻。
        logger.info("开始抓取新闻...")
        # 抓取最多 30 条 AI 新闻；数量上限由这里传入 fetch_ai_news。
        news_list = fetch_ai_news(30)
        # 记录实际抓到的新闻数量。
        logger.info(f"获取到 {len(news_list)} 条 AI 新闻")

        # 准备一个列表，用来保存已经生成摘要的新闻。
        summarized = []
        # 逐条处理抓到的新闻。
        for news in news_list:
            # 每条新闻单独 try，避免一条失败影响其他新闻。
            try:
                # 调用大模型，根据标题和链接生成中文摘要。
                summary = summarize_news(news["title"], news.get("url", ""))
                # 把摘要写回当前新闻字典，后面邮件会用到。
                news["summary"] = summary
                # 把当前新闻加入邮件待发送列表。
                summarized.append(news)
                # 把新闻源的 Unix 时间戳转换成 datetime，便于写入数据库。
                source_time = datetime.fromtimestamp(news["time"])
                # 默认不保存向量；只有开启 ENABLE_EMBEDDING 时才生成。
                embedding = None
                # 判断是否开启本地 embedding 功能。
                if ENABLE_EMBEDDING:
                    # embedding 单独 try，避免向量化失败影响邮件发送。
                    try:
                        # 把摘要文本转换成向量，用于后续 RAG 相似检索。
                        embedding = get_embedding(summary)
                    # 捕获向量化失败的异常。
                    except Exception as e:
                        # 记录警告，但继续把新闻以无向量形式入库。
                        logger.warning(f"Embedding failed, inserting without vector: {news['title']} - {e}")
                # 把标题、链接、摘要、分数、时间、向量写入 PostgreSQL。
                insert_news(news["title"], news.get("url", ""), summary, news["score"], source_time, embedding)
                # 记录当前新闻处理完成，debug 级别默认不会显示。
                logger.debug(f"已处理: {news['title'][:30]}")
            # 捕获单条新闻处理过程中的任何异常。
            except Exception as e:
                # 记录失败原因，方便你排查是摘要失败还是入库失败。
                logger.error(f"处理新闻失败: {news['title']} - {e}")
                # 给失败新闻一个兜底摘要，避免邮件里缺字段。
                news["summary"] = "(处理失败)"
                # 即使处理失败，也把新闻放进邮件里，让你知道是哪条失败。
                summarized.append(news)

        # 根据天气和新闻摘要生成 HTML 邮件正文。
        html = create_html_content(weather, summarized)
        # 把 HTML 邮件发送到配置的收件邮箱。
        send_email(html)
        # 记录整次任务结束。
        logger.info("邮件发送完成，任务结束。")
    # 捕获每日任务整体异常，例如数据库连接失败、天气接口失败等。
    except Exception:
        # logger.exception 会自动带上完整错误堆栈。
        logger.exception("每日任务执行失败")


# 只有直接运行 python main.py 时，下面的代码才会执行。
if __name__ == "__main__":
    # 启动后先立刻执行一次任务，方便你手动测试。
    job()

    # 注册一个定时任务：每天 08:00 自动执行 job。
    schedule.every().day.at("08:00").do(job)
    # 记录定时任务已经启动。
    logger.info("定时任务已启动，每天 08:00 执行")
    # 进入无限循环，让程序常驻后台等待定时任务。
    while True:
        # 检查当前时间是否有需要执行的定时任务。
        schedule.run_pending()
        # 每 60 秒检查一次，避免 CPU 空转。
        time.sleep(60)
