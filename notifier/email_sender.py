# 导入 smtplib，用来连接 SMTP 邮箱服务器并发送邮件。
import smtplib
# 导入 datetime，用来生成邮件标题和页脚时间。
from datetime import datetime
# 导入 MIMEMultipart，用来创建多部分邮件。
from email.mime.multipart import MIMEMultipart
# 导入 MIMEText，用来把 HTML 内容放进邮件正文。
from email.mime.text import MIMEText
# 导入 escape，用来转义 HTML 特殊字符，避免标题里有特殊符号破坏页面。
from html import escape

# 导入邮箱相关配置。
from config import RECEIVER_EMAIL, SENDER_EMAIL, SENDER_PASSWORD, SMTP_PORT, SMTP_SERVER


# 定义生成 HTML 邮件正文的函数。
def create_html_content(weather_info: dict, news_summaries: list) -> str:
    # 生成天气模块 HTML。
    weather_html = f"""
    <div style="background:#f0f8ff; padding:15px; border-radius:8px; margin-bottom:20px;">
        <h2 style="color:#333;">今日天气 - {escape(str(weather_info['city']))}</h2>
        <p>天气：{escape(str(weather_info['weather']))}，温度 {escape(str(weather_info['temperature']))}°C</p>
        <p>风向：{escape(str(weather_info['winddirection']))}，湿度 {escape(str(weather_info['humidity']))}%</p>
        <p>更新时间：{escape(str(weather_info['reporttime']))}</p>
    </div>
    """

    # 准备新闻列表 HTML 字符串。
    news_items = ""
    # 遍历每条已经生成摘要的新闻。
    for i, news in enumerate(news_summaries, 1):
        # 读取新闻地区，例如国内/国外。
        region = escape(str(news.get("region", "新闻")))
        # 读取新闻来源，例如 36Kr、TechCrunch AI。
        source = escape(str(news.get("source", news.get("by", "Unknown"))))
        # 读取新闻分数；RSS 来源通常没有分数。
        score = news.get("score", 0)
        # 转义新闻标题。
        title = escape(str(news["title"]))
        # 转义新闻链接，并允许作为 HTML 属性使用。
        url = escape(str(news.get("url", "")), quote=True)
        # 转义中文摘要。
        summary = escape(str(news.get("summary", "")))

        # 如果有分数，就在来源标签后展示 points。
        score_html = f" · {score} points" if score else ""
        # 把当前新闻拼成一段 HTML，并追加到 news_items。
        news_items += f"""
        <div style="margin-bottom:15px; border-bottom:1px solid #eee; padding-bottom:10px;">
            <p style="font-size:14px; color:#555; margin:0 0 5px 0;">
                <strong>{i}. </strong>
                <span style="color:#888;">[{region} · {source}{score_html}]</span>
                <a href="{url}" style="color:#1a0dab; text-decoration:none;">{title}</a>
            </p>
            <p style="margin:0; color:#333; font-size:13px;">{summary}</p>
        </div>
        """

    # 拼出完整 HTML 邮件页面。
    html = f"""
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family: 'Segoe UI', Arial, sans-serif; max-width:700px; margin:auto; padding:20px;">
        <h1 style="color:#2c3e50;">AI 行业早报</h1>
        <p style="color:#7f8c8d;">{datetime.now().strftime('%Y-%m-%d %A')}</p>
        {weather_html}
        <h2 style="color:#2c3e50;">今日 AI 要闻</h2>
        {news_items}
        <hr>
        <p style="color:#999; font-size:12px; text-align:center;">
            由 DeepSeek AI 助手自动生成 · {datetime.now().strftime('%Y-%m-%d %H:%M')}
        </p>
    </body>
    </html>
    """
    # 返回完整 HTML 字符串。
    return html


# 定义发送邮件函数。
def send_email(html_content: str):
    # 创建一封支持多格式内容的邮件。
    msg = MIMEMultipart("alternative")
    # 设置邮件标题。
    msg["Subject"] = f"AI 行业早报 - {datetime.now().strftime('%Y-%m-%d')}"
    # 设置发件人。
    msg["From"] = SENDER_EMAIL
    # 设置收件人。
    msg["To"] = RECEIVER_EMAIL

    # 把 HTML 内容作为邮件正文添加进去。
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    # 用 try 捕获邮件发送失败。
    try:
        # 连接 SMTP 服务器。
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            # 启用 TLS 加密。
            server.starttls()
            # 登录发件邮箱。
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            # 发送邮件。
            server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        # 发送成功后在终端打印提示。
        print("邮件发送成功！")
    # 捕获发送过程中的异常。
    except Exception as e:
        # 打印失败原因。
        print(f"邮件发送失败: {e}")
