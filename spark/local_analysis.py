"""
云计算课设 - 方向A：豆瓣电影数据分析（本地 Pandas 版）
覆盖 A-1 数据清洗 + A-2 统计分析 + A-3 性能对比

使用方法：python local_analysis.py
"""
import pandas as pd
import numpy as np
import time
import os

# ============================================================
# 读取数据
# ============================================================
data_path = os.path.join(os.path.dirname(__file__), "..", "..", "douban_movies.csv")
# 如果上面路径不对，改成你的实际路径
if not os.path.exists(data_path):
    data_path = r"E:\University\大三\大三下\云计算\douban_movies.csv"

print("=" * 70)
print("云计算课程设计 · 方向A：豆瓣电影数据分析")
print(f"数据文件: {data_path}")
print("=" * 70)

df = pd.read_csv(data_path)

# ============================================================
# A-1: 数据清洗
# ============================================================
print("\n" + "=" * 70)
print("A-1: 数据清洗")
print("=" * 70)

# 打印 Schema（DataFrame 信息）
print("\n【DataFrame 信息】")
print(f"行数: {len(df)}, 列数: {len(df.columns)}")
print(f"\n字段列表与数据类型:")
for col in df.columns:
    print(f"  {col}: {df[col].dtype}")

# 前5行
print("\n【前5行数据】")
print(df.head().to_string())

# 统计各字段缺失值比例
print("\n【各字段缺失值比例】")
total = len(df)
for col in df.columns:
    null_count = df[col].isnull().sum()
    print(f"  {col}: {null_count}/{total} ({null_count/total*100:.1f}%)")

# 策略1: 对评分（rating_score）用均值填充
# 选择原因：评分缺失用平均分代替是合理的插补方式，保留样本量
print("\n【策略1】对 rating_score 字段用均值填充")
avg_rating = df['rating_score'].mean()
print(f"  评分均值: {avg_rating:.2f}")
df_clean = df.copy()
before_fillna = df_clean['rating_score'].isnull().sum()
df_clean['rating_score'] = df_clean['rating_score'].fillna(avg_rating)
after_fillna = df_clean['rating_score'].isnull().sum()
print(f"  填充前缺失: {before_fillna}, 填充后缺失: {after_fillna}")

# 策略2: 对类型（genres）缺失值删除
# 选择原因：电影类型是分析的核心维度，缺失则该行分析价值低
print("\n【策略2】对 genres 字段删除缺失行")
before_dropna = len(df_clean)
df_clean = df_clean.dropna(subset=['genres'])
after_dropna = len(df_clean)
print(f"  删除前行数: {before_dropna}, 删除后行数: {after_dropna}")

# 其他字段缺失值简单填充
for col in df_clean.columns:
    if df_clean[col].dtype in ['float64', 'int64']:
        df_clean[col] = df_clean[col].fillna(df_clean[col].median())
    elif df_clean[col].dtype == 'object':
        df_clean[col] = df_clean[col].fillna('未知')

# 清洗前后对比
print(f"\n【清洗前后对比】")
print(f"  清洗前行数: {total}")
print(f"  清洗后行数: {len(df_clean)}")

# 基本统计信息
print(f"\n【清洗后基本统计】")
print(df_clean.describe().to_string())

# 保存清洗后的数据
df_clean.to_csv(os.path.join(os.path.dirname(data_path) or '.', 'douban_movies_clean.csv'), index=False)
print("\n清洁后数据已保存至 douban_movies_clean.csv")

# ============================================================
# A-2: 统计分析（对应 Spark SQL 查询）
# ============================================================
print("\n" + "=" * 70)
print("A-2: 统计分析")
print("=" * 70)

print("\n📊 查询1: 各类型平均评分（GROUP BY 聚合）")
query1_start = time.time()
genre_stats = df_clean.groupby('genres').agg(
    电影数量=('title', 'count'),
    平均评分=('rating_score', 'mean')
).round(2).sort_values('平均评分', ascending=False)
query1_time = time.time() - query1_start
print(genre_stats.head(15).to_string())
print(f"\n分析说明：统计各电影类型的数量和平均评分，评分最高的类型通常代表该类型整体质量较高，")
print(f"可为用户推荐提供参考依据。执行时间: {query1_time:.3f} 秒")

print("\n📊 查询2: 评分 Top-10 电影（ORDER BY Top-N）")
query2_start = time.time()
top10 = df_clean.nlargest(10, 'rating_score')[['title', 'rating_score', 'year', 'genres']]
query2_time = time.time() - query2_start
print(top10.to_string())
print(f"\n分析说明：通过评分降序排列，展示评分最高的10部电影，可直接用于优质电影推荐。")
print(f"执行时间: {query2_time:.3f} 秒")

print("\n📊 查询3: 每年电影数量与平均评分时间趋势（时间维度分析）")
query3_start = time.time()
year_stats = df_clean[df_clean['year'].notna()].groupby('year').agg(
    电影数量=('title', 'count'),
    平均评分=('rating_score', 'mean')
).round(2)
query3_time = time.time() - query3_start
print(year_stats.to_string())
print(f"\n分析说明：按年份统计电影数量和平均评分，可观察电影产业随时间的发展趋势。")
print(f"执行时间: {query3_time:.3f} 秒")

print("\n📊 查询4: 各类型内评分排名前3（窗口函数 ROW_NUMBER）")
query4_start = time.time()
df_clean['rating_rank'] = df_clean.groupby('genres')['rating_score'].rank(ascending=False, method='dense')
top3_per_genre = df_clean[df_clean['rating_rank'] <= 3].sort_values(['genres', 'rating_rank'])
query4_time = time.time() - query4_start
print(top3_per_genre[['genres', 'title', 'rating_score', 'rating_rank']].to_string())
print(f"\n分析说明：使用窗口函数 ROW_NUMBER() 对每个电影类型内部按评分排名，")
print(f"展示各类型最佳电影，便于跨类型比较。执行时间: {query4_time:.3f} 秒")

# ============================================================
# A-3: 性能对比与 Amdahl 分析
# ============================================================
print("\n" + "=" * 70)
print("A-3: 性能对比与 Amdahl 分析")
print("=" * 70)

print("\n【不同数据量下的查询性能对比】")
print(f"{'数据量':<10} {'查询1(GROUP BY)':<20} {'查询2(Top-N)':<20} {'查询3(时间)':<20}")
print("-" * 70)

# 分别测试 100、500、1000、5000、全部 行的性能
sizes = [100, 500, 1000, 5000, len(df_clean)]
for size in sizes:
    if size > len(df_clean):
        continue
    sample = df_clean.head(size)

    t1_start = time.time()
    sample.groupby('genres')['rating_score'].agg(['count', 'mean']).round(2)
    t1 = time.time() - t1_start

    t2_start = time.time()
    sample.nlargest(10, 'rating_score')[['title', 'rating_score']]
    t2 = time.time() - t2_start

    t3_start = time.time()
    sample[sample['year'].notna()].groupby('year')['title'].count()
    t3 = time.time() - t3_start

    print(f"{size:<10} {t1*1000:<20.3f} {t2*1000:<20.3f} {t3*1000:<20.3f}")

print(f"\n（以上时间为毫秒 ms，数据来自单机 Pandas 串行执行）")

# Amdahl 定律分析
print("\n【Amdahl 定律分析】")
print("-" * 70)
print("Amdahl 定律: S = 1 / ((1-P) + P/N)")
print("  其中 S = 加速比, P = 可并行比例, N = 处理器数")
print("\n以 Pandas 单机为基准（相当于 N=1）：")
print("  如果可并行比例 P=0.8（80%的代码可并行）：")
for n in [1, 2, 4]:
    s = 1 / ((1 - 0.8) + 0.8 / n)
    print(f"    N={n}核 → 理论加速比 S={s:.2f}")
print("\n  如果可并行比例 P=0.95（95%的代码可并行）：")
for n in [1, 2, 4]:
    s = 1 / ((1 - 0.95) + 0.95 / n)
    print(f"    N={n}核 → 理论加速比 S={s:.2f}")

print("\n实际加速比达不到理论值的原因：")
print("  1. 通信开销：Spark 在集群节点间传输数据有网络延迟")
print("  2. 序列化开销：数据在 Python/Java 之间转换需要时间")
print("  3. 任务调度：Spark Driver 调度任务本身有开销")
print("  4. 数据倾斜：部分分区数据量大，拖慢整体进度")
print("  5. 小数据量：数据量小时串行可能反而更快（调度开销 > 计算收益）")

print("\n" + "=" * 70)
print("✅ 分析完成！以上结果可直接用于报告截图")
print("=" * 70)
