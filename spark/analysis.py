"""
Spark 数据分析完整脚本（方向A）
包含：
  A-1: 数据清洗
  A-2: Spark SQL 统计分析
  A-3: 性能对比辅助函数
"""
import time
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, when, isnan, isnull, year, month, desc, avg

spark = SparkSession.builder.appName("MovieAnalysis").getOrCreate()

# ============================================================
# A-1: 数据清洗
# ============================================================
print("=" * 60)
print("A-1: 数据清洗")
print("=" * 60)

# 读取 OBS 上的电影数据集（路径由教师提供）
df = spark.read.csv("s3a://<BUCKET>/douban_movies.csv", header=True, inferSchema=True)

# 打印 Schema 和前 5 行
print("Schema:")
df.printSchema()
print("前 5 行:")
df.show(5)

# 统计各字段缺失值比例
print("各字段缺失值比例:")
total_rows = df.count()
for col_name in df.columns:
    null_count = df.filter(col(col_name).isNull() | isnan(col(col_name))).count()
    print(f"  {col_name}: {null_count}/{total_rows} ({null_count/total_rows*100:.1f}%)")

# 策略1: 对缺失比例低的字段（如 rating）用 fillna 填充均值
# 选择原因：评分缺失可合理用平均分替代，保留数据量
df_clean = df.fillna({"rating": df.select(avg("rating")).collect()[0][0]})

# 策略2: 对缺失比例高的字段（如 genre）用 dropna 删除
# 选择原因：类型缺失意味着该行信息不完整，分析时无价值
df_clean = df_clean.dropna(subset=["genre"])

print(f"清洗前行数: {total_rows}")
print(f"清洗后行数: {df_clean.count()}")

# 基本统计信息
df_clean.describe().show()

# ============================================================
# A-2: Spark SQL 统计分析
# ============================================================
print("=" * 60)
print("A-2: Spark SQL 统计分析")
print("=" * 60)

df_clean.createOrReplaceTempView("movies")

# 查询1: GROUP BY 聚合 —— 按电影类型统计平均评分
print("查询1: 各类型平均评分（GROUP BY 聚合）")
query1 = """
    SELECT genre, COUNT(*) AS count, ROUND(AVG(rating), 2) AS avg_rating
    FROM movies
    GROUP BY genre
    ORDER BY avg_rating DESC
"""
spark.sql(query1).show(20)
print("分析说明：统计各电影类型的平均评分和数量，可以找出评分最高的类型类型，为推荐提供依据。")

# 查询2: ORDER BY Top-N —— 评分最高的 10 部电影
print("查询2: 评分 Top-10 电影（ORDER BY Top-N）")
query2 = """
    SELECT title, rating, year
    FROM movies
    ORDER BY rating DESC
    LIMIT 10
"""
spark.sql(query2).show(10)
print("分析说明：通过评分降序排列，找出评分最高的 10 部电影，可直接用于推荐榜单。")

# 查询3: 时间维度趋势分析 —— 每年电影数量和平均评分
print("查询3: 每年电影数量和平均评分（时间维度分析）")
query3 = """
    SELECT year, COUNT(*) AS movie_count, ROUND(AVG(rating), 2) AS avg_rating
    FROM movies
    WHERE year IS NOT NULL
    GROUP BY year
    ORDER BY year
"""
spark.sql(query3).show(30)
print("分析说明：按年份统计电影数量和平均评分，观察电影产业变化趋势和评分变化规律。")

# 查询4: JOIN + 窗口函数 —— 各类型评分排名（窗口函数）
print("查询4: 各类型内评分排名前 3（窗口函数）")
query4 = """
    SELECT genre, title, rating, rank
    FROM (
        SELECT genre, title, rating,
               ROW_NUMBER() OVER (PARTITION BY genre ORDER BY rating DESC) AS rank
        FROM movies
        WHERE rating IS NOT NULL
    )
    WHERE rank <= 3
    ORDER BY genre, rank
"""
spark.sql(query4).show(30)
print("分析说明：使用窗口函数 ROW_NUMBER() 对每个电影类型内部分别按评分排名，展示各类型最佳电影。")

# ============================================================
# A-3: 性能对比测量函数（供后续对比用）
# ============================================================
print("=" * 60)
print("A-3: 性能对比（执行时间测量）")
print("=" * 60)

def measure_spark_query(sql_text, label=""):
    """测量 Spark SQL 查询执行时间"""
    start = time.time()
    spark.sql(sql_text).collect()
    elapsed = time.time() - start
    print(f"  Spark [{label}]: {elapsed:.3f} 秒")
    return elapsed

# 测量查询1（GROUP BY）在不同 executor 配置下的性能
measure_spark_query(query1, "2 executors - GROUP BY")
measure_spark_query(query2, "2 executors - Top-N")

spark.stop()
print("Spark Session 已关闭。")
