"""
并行矩阵乘法（MPI 实现）
题目1：Scatter 分发行块，Gather 收集结果

通信模式：
  1. rank=0 将矩阵 A 按行分块 → Scatter 发送给各进程
  2. rank=0 将完整矩阵 B → Bcast 广播给各进程
  3. 各进程计算自己的部分结果
  4. 各进程将结果块 → Gather 发送回 rank=0
  5. rank=0 合并得到完整结果
"""
from mpi4py import MPI
import numpy as np
import time

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

N = 800  # 矩阵规模 N×N

def serial_matmul(A, B):
    """串行矩阵乘法（基准对照）"""
    return A @ B

def parallel_matmul(N, rank, size, comm):
    """MPI 并行矩阵乘法"""
    # rank=0 生成完整矩阵
    if rank == 0:
        A = np.random.rand(N, N).astype(np.float64)
        B = np.random.rand(N, N).astype(np.float64)
    else:
        A = None
        B = np.empty((N, N), dtype=np.float64)

    # Bcast：将矩阵 B 广播给所有进程
    comm.Bcast(B, root=0)

    # 计算每个进程需要处理的行数
    local_n = N // size
    remainder = N % size

    # 分配行数（前 remainder 个进程多分一行）
    counts = [local_n + (1 if i < remainder else 0) for i in range(size)]
    displs = [sum(counts[:i]) for i in range(size)]

    # 准备本地接收缓冲区
    local_A = np.empty((counts[rank], N), dtype=np.float64)

    # Scatterv：将矩阵 A 按行分发给各进程
    comm.Scatterv([A, counts, displs, MPI.DOUBLE], local_A, root=0)

    # 各进程计算自己的部分结果
    local_C = local_A @ B

    # Gatherv：收集各进程的结果
    if rank == 0:
        C = np.empty((N, N), dtype=np.float64)
    else:
        C = None
    comm.Gatherv(local_C, [C, counts, displs, MPI.DOUBLE], root=0)

    return C

# ===== 主程序 =====
start = time.time()
C_parallel = parallel_matmul(N, rank, size, comm)
parallel_time = time.time() - start

if rank == 0:
    # 串行版（只在 rank=0 上运行）
    A = np.random.rand(N, N).astype(np.float64)
    B = np.random.rand(N, N).astype(np.float64)
    start = time.time()
    C_serial = serial_matmul(A, B)
    serial_time = time.time() - start

    # 验证结果一致性
    diff = np.max(np.abs(C_serial - C_parallel))
    print(f"矩阵规模: {N}×{N}")
    print(f"进程数: {size}")
    print(f"串行时间: {serial_time:.3f} 秒")
    print(f"并行时间: {parallel_time:.3f} 秒")
    print(f"加速比: {serial_time/parallel_time:.2f}")
    print(f"最大误差: {diff:.2e}")
    print(f"结果一致性: {'✅ 通过' if diff < 1e-10 else '❌ 失败'}")
