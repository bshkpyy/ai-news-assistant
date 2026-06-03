# 导入 numpy，用来判断 embedding 是否是 numpy 数组。
import numpy as np
# 导入 psycopg2，用来连接 PostgreSQL 数据库。
import psycopg2

# 导入数据库连接配置。
from config import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER


# 本地 sentence-transformers 模型输出 384 维向量。
EMBEDDING_DIMENSIONS = 384


# 定义获取数据库连接的函数。
def get_connection():
    # 使用 .env 中的数据库配置创建 PostgreSQL 连接。
    return psycopg2.connect(
        # 数据库主机地址。
        host=DB_HOST,
        # 数据库端口。
        port=DB_PORT,
        # 数据库名称。
        dbname=DB_NAME,
        # 数据库用户名。
        user=DB_USER,
        # 数据库密码。
        password=DB_PASSWORD,
    )


# 定义数据库初始化函数。
def init_db():
    # 创建数据库连接。
    conn = get_connection()
    # 创建游标，用来执行 SQL。
    cur = conn.cursor()
    # 启用 pgvector 扩展；如果已经启用，不会重复创建。
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    # 创建新闻表；如果表已经存在，不会重复创建。
    cur.execute(
        f"""
        CREATE TABLE IF NOT EXISTS news_articles (
            id SERIAL PRIMARY KEY,
            title TEXT,
            url TEXT,
            summary TEXT,
            score INTEGER,
            source_time TIMESTAMP,
            embedding vector({EMBEDDING_DIMENSIONS})
        );
        """
    )
    # 查询 embedding 字段当前的 pgvector 维度信息。
    cur.execute(
        """
        SELECT atttypmod
        FROM pg_attribute
        WHERE attrelid = 'news_articles'::regclass
          AND attname = 'embedding';
        """
    )
    # 取出 embedding 字段的 typmod；pgvector 的 typmod 通常是维度 + 4。
    embedding_typmod = cur.fetchone()[0]
    # 计算当前代码期望的 typmod。
    expected_typmod = EMBEDDING_DIMENSIONS + 4
    # 如果数据库字段维度不是当前 384 维，就进行迁移。
    if embedding_typmod not in (-1, expected_typmod):
        # 迁移维度时旧向量无法保留，所以用 NULL 清空旧 embedding。
        cur.execute(
            f"""
            ALTER TABLE news_articles
            ALTER COLUMN embedding TYPE vector({EMBEDDING_DIMENSIONS})
            USING NULL;
            """
        )
    # 提交数据库结构变更。
    conn.commit()
    # 关闭游标。
    cur.close()
    # 关闭数据库连接。
    conn.close()
    # 在终端打印初始化完成。
    print("数据库初始化完成。")


# 定义插入新闻的函数。
def insert_news(title, url, summary, score, source_time, embedding):
    # 创建数据库连接。
    conn = get_connection()
    # 创建游标。
    cur = conn.cursor()
    # 如果 embedding 是 numpy 数组，就转成普通 list，方便 psycopg2 写入。
    embedding_list = embedding.tolist() if isinstance(embedding, np.ndarray) else embedding
    # 执行插入 SQL，把一条新闻写入 news_articles 表。
    cur.execute(
        """
        INSERT INTO news_articles (title, url, summary, score, source_time, embedding)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        # 这里用参数化 SQL，避免字符串拼接带来的 SQL 注入风险。
        (title, url, summary, score, source_time, embedding_list),
    )
    # 提交插入操作。
    conn.commit()
    # 关闭游标。
    cur.close()
    # 关闭连接。
    conn.close()


# 定义相似新闻检索函数，用于 RAG。
def search_similar(query_embedding, limit=5):
    # 创建数据库连接。
    conn = get_connection()
    # 创建游标。
    cur = conn.cursor()
    # 如果查询向量是 numpy 数组，就转成普通 list。
    embedding_list = query_embedding.tolist() if isinstance(query_embedding, np.ndarray) else query_embedding
    # 使用 pgvector 的 <=> 余弦距离查找最相似的新闻。
    cur.execute(
        """
        SELECT title, url, summary, score, source_time, 1 - (embedding <=> %s::vector) AS similarity
        FROM news_articles
        WHERE embedding IS NOT NULL
        ORDER BY embedding <=> %s::vector
        LIMIT %s;
        """,
        # 第一个向量用于计算相似度，第二个向量用于排序。
        (embedding_list, embedding_list, limit),
    )
    # 取回查询结果。
    results = cur.fetchall()
    # 关闭游标。
    cur.close()
    # 关闭连接。
    conn.close()
    # 返回相似新闻列表。
    return results
