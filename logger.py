# 导入 Python 标准库 logging，用来记录程序运行日志。
import logging


# 定义一个创建 logger 的函数；name 是日志记录器的名字。
def setup_logger(name="ai_news"):
    # 根据名字获取 logger；同名 logger 会复用。
    logger = logging.getLogger(name)
    # 设置 logger 最低输出级别为 INFO。
    logger.setLevel(logging.INFO)
    # 如果 logger 已经添加过 handler，就直接返回，避免重复打印日志。
    if logger.handlers:
        # 返回已经配置好的 logger。
        return logger

    # 创建控制台日志处理器，用来把日志打印到终端。
    console_handler = logging.StreamHandler()
    # 设置控制台日志最低输出级别为 INFO。
    console_handler.setLevel(logging.INFO)
    # 创建统一日志格式：时间 - 模块名 - 级别 - 消息。
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    # 给控制台处理器设置日志格式。
    console_handler.setFormatter(formatter)
    # 把控制台处理器添加到 logger。
    logger.addHandler(console_handler)

    # 创建文件日志处理器，把日志写入 app.log。
    file_handler = logging.FileHandler("app.log", encoding="utf-8")
    # 设置文件日志最低输出级别为 INFO。
    file_handler.setLevel(logging.INFO)
    # 给文件处理器设置同样的日志格式。
    file_handler.setFormatter(formatter)
    # 把文件处理器添加到 logger。
    logger.addHandler(file_handler)
    # 返回配置完成的 logger。
    return logger
