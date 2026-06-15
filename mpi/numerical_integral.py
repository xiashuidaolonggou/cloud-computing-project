"""
数值积分（梯形法）MPI 并行实现
题目2：Scatter 子区间，Reduce 求和

通信模式：
  1. rank=0 将积分区间均分 → Scatter 发送各子区间给各进程
  2. 各进程用梯形法计算子区间积分
  3. Reduce：各进程的局部积分值 → MPI.SUM 归约到 rank=0
"""
from mpi4py import MPI
import numpy as np
import time

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

def f(x):
    """被积函数 f(x) = 4/(1+x²)，在 [0,1] 上积分为 π"""
    return 4.0 / (1.0 + x * x)

def serial_integral(N):
    """串行梯形法求积分（基准对照）"""
    a, b = 0.0, 1.0
    h = (b - a) / N
    total = 0.5 * (f(a) + f(b))
    for i in range(1, N):
        total += f(a + i * h)
    return total * h

def parallel_integral(N, rank, size, comm):
    """MPI 并行梯形法"""
    a, b = 0.0, 1.0
    h = (b - a) / N

    # 每个进程计算局部梯形和
    local_n = N // size
    local_start = rank * local_n
    local_end = (rank + 1) * local_n

    local_sum = 0.0
    for i in range(local_start, local_end):
        x = a + (i + 0.5) * h  # 取中点
        local_sum += f(x)

    # Reduce：将所有进程的局部和汇总到 rank=0
    total_sum = comm.reduce(local_sum, op=MPI.SUM, root=0)

    if rank == 0:
        return (total_sum + 0.5 * (f(a) + f(b))) * h
    return None

# ===== 主程序 =====
N = 10_000_000  # 积分区间数

start = time.time()
pi_parallel = parallel_integral(N, rank, size, comm)
parallel_time = time.time() - start

if rank == 0:
    start = time.time()
    pi_serial = serial_integral(N)
    serial_time = time.time() - start

    print(f"积分区间数: {N:,}")
    print(f"进程数: {size}")
    print(f"串行结果: π ≈ {pi_serial:.8f}, 时间: {serial_time:.3f} 秒")
    print(f"并行结果: π ≈ {pi_parallel:.8f}, 时间: {parallel_time:.3f} 秒")
    print(f"加速比: {serial_time/parallel_time:.2f}")
    print(f"结果一致性: {'✅ 通过' if abs(pi_serial - pi_parallel) < 1e-10 else '❌ 失败'}")
