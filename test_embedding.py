# 导入本地 embedding 模型名和向量化函数。
from processors.embedder import EMBEDDING_MODEL_NAME, get_embedding


# 只有直接运行 python test_embedding.py 时才执行测试。
if __name__ == "__main__":
    # 用一段中英文混合文本测试向量化。
    emb = get_embedding("测试文本：国内外 AI 新闻向量化")
    # 打印当前使用的本地 embedding 模型。
    print(f"本地 Embedding 可用：{EMBEDDING_MODEL_NAME}")
    # 打印向量维度，正常应该是 384。
    print(f"维度：{len(emb)}")
