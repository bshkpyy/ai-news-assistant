# 导入 numpy，用来把模型输出转换成数据库更好处理的 float32 数组。
import numpy as np
# 导入 SentenceTransformer，用来加载本地 embedding 模型。
from sentence_transformers import SentenceTransformer


# 设置本地 embedding 模型名；这个模型支持中文和英文。
EMBEDDING_MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
# 设置向量维度；这个模型输出 384 维向量。
EMBEDDING_DIMENSIONS = 384


# 定义模型加载函数，封装“优先读本地缓存，缺失时再联网下载”的逻辑。
def _load_model(model_name: str) -> SentenceTransformer:
    # 先尝试只从本地缓存加载，避免每次启动都访问 Hugging Face。
    try:
        # local_files_only=True 表示不联网，只查本地缓存。
        return SentenceTransformer(model_name, local_files_only=True)
    # 如果本地缓存没有模型，就进入 except。
    except Exception:
        # 允许联网下载模型；首次运行时会走这里。
        return SentenceTransformer(model_name)


# 程序启动时加载默认 embedding 模型。
model = _load_model(EMBEDDING_MODEL_NAME)


# 定义获取文本向量的函数。
def get_embedding(text: str, model_name: str | None = None) -> np.ndarray:
    # 如果调用者指定了不同模型，就临时加载指定模型。
    if model_name and model_name != EMBEDDING_MODEL_NAME:
        # 加载调用者指定的模型。
        custom_model = _load_model(model_name)
        # 把文本转向量，并转换成 float32，节省存储空间。
        return custom_model.encode(text).astype(np.float32)
    # 使用默认模型把文本转成 384 维向量，并转换成 float32。
    return model.encode(text).astype(np.float32)
