"""
并行奇偶换序排序（MPI 实现）
题目3：相邻进程比较与交换

通信模式：
  1. 各进程先对自己的数据做本地排序
  2. 偶数轮次：偶数编号进程与右邻居比较交换（Send/Recv）
  3. 奇数轮次：奇数编号进程与右邻居比较交换（Send/Recv）
  4. 重复直到全局有序
"""
from mpi4py import MPI
import numpy as np
import time

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

def serial_sort(data):
    """串行冒泡排序（基准对照）"""
    arr = data.copy()
    n = len(arr)
    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr

def parallel_odd_even_sort(local_data, rank, size, comm):
    """MPI 并行奇偶换序排序"""
    n_local = len(local_data)
    arr = sorted(local_data)  # 先本地排序

    for phase in range(size):  # 最多需要 size 轮
        if phase % 2 == 0:
            # 偶数轮次：偶数 rank 与右邻居交换
            partner = rank + 1 if rank % 2 == 0 else rank - 1
        else:
            # 奇数轮次：奇数 rank 与右邻居交换
            partner = rank + 1 if rank % 2 == 1 else rank - 1

        if 0 <= partner < size:
            if rank < partner:
                # 发送自己的数据给右邻居
                comm.Send(arr, dest=partner)
                # 接收右邻居的数据
                neighbor_data = np.empty(n_local, dtype=np.float64)
                comm.Recv(neighbor_data, source=partner)
                # 合并并保留较小的一半
                merged = sorted(np.concatenate([arr, neighbor_data]))
                arr = merged[:n_local]
            else:
                # 接收左邻居的数据
                neighbor_data = np.empty(n_local, dtype=np.float64)
                comm.Recv(neighbor_data, source=partner)
                # 发送自己的数据给左邻居
                comm.Send(arr, dest=partner)
                # 合并并保留较大的一半
                merged = sorted(np.concatenate([arr, neighbor_data]))
                arr = merged[n_local:]

    return arr

# ===== 主程序 =====
np.random.seed(42)
N = 1000  # 每个进程本地数据量

# 生成数据
local_data = np.random.rand(N).astype(np.float64)

start = time.time()
sorted_local = parallel_odd_even_sort(local_data, rank, size, comm)
parallel_time = time.time() - start

# Gather 收集所有结果到 rank=0
all_sorted = comm.gather(sorted_local, root=0)

if rank == 0:
    # 串行版
    all_data = np.random.rand(N * size).astype(np.float64)
    start = time.time()
    serial_result = serial_sort(all_data)
    serial_time = time.time() - start

    # 合并并行结果
    parallel_result = np.concatenate(all_sorted)

    # 验证
    match = np.allclose(serial_result, parallel_result)
    print(f"总数据量: {N * size}")
    print(f"进程数: {size}")
    print(f"串行时间: {serial_time:.3f} 秒")
    print(f"并行时间: {parallel_time:.3f} 秒")
    print(f"加速比: {serial_time/parallel_time:.2f}")
    print(f"结果一致性: {'✅ 通过' if match else '❌ 失败'}")
