import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

nl = 12
nt = 9

# 布尔矩阵
block = np.zeros((nl, nt), dtype=bool)

# 设置 True 的位置
block[:, 0] = True
block[:, 1] = True
block[:, 8] = True

# 数值矩阵用于颜色
data = np.zeros_like(block, dtype=int)
data[0, block[0, :]] = 1
data[-2, block[-2, :]] = 2
data[-1, block[-1, :]] = 3
for i in range(1, nl-2):
    data[i, block[i, :]] = 4

# 绘图
fig, ax = plt.subplots(figsize=(8, 8))

# 颜色映射
cmap = plt.cm.colors.ListedColormap(['white', '#FF6B6B', '#98FB98', '#4ECDC4', '#FFE66D'])
bounds = [0, 1, 2, 3, 4, 5]
norm = plt.cm.colors.BoundaryNorm(bounds, cmap.N)

im = ax.imshow(data, cmap=cmap, norm=norm, aspect='equal')

# 坐标轴：行列号
ax.set_xticks(range(nt))
ax.set_yticks(range(nl))
ax.set_xticklabels(range(1, nt+1))
ax.set_yticklabels(range(1, nl+1))

# 格子边框（黑色网格线）
ax.set_xticks(np.arange(-0.5, nt, 1), minor=True)
ax.set_yticks(np.arange(-0.5, nl, 1), minor=True)
ax.grid(which='minor', color='black', linewidth=0.5, linestyle='-')

# 可选：在每个 True 格子中心加小圆点
for i in range(nl):
    for j in range(nt):
        if data[i, j] != 0:
            ax.text(j, i, f'({i}-{j})', ha='center', va='center', color='black', fontsize=8)

# ========== 高亮相邻 True 格子之间的共享边 ==========
highlight_color = 'red'
linewidth = 2.5

# 1. 向右检查（垂直边）
for i in range(nl):
    for j in range(nt-1):
        if block[i, j] and block[i, j+1]:
            ax.plot([j+0.5, j+0.5], [i-0.5, i+0.5], color=highlight_color, linewidth=linewidth)

# 2. 向下检查（水平边）
for i in range(nl-1):
    for j in range(nt):
        if block[i, j] and block[i+1, j]:
            ax.plot([j-0.5, j+0.5], [i+0.5, i+0.5], color=highlight_color, linewidth=linewidth)

# 3. 行方向环状接触：检查每行的第一个和最后一个格子
for i in range(nl):
    if block[i, 0] and block[i, -1]:
        # 左边界高亮线：x = -0.5
        ax.plot([-0.5, -0.5], [i-0.5, i+0.5], color=highlight_color, linewidth=linewidth)
        # 右边界高亮线：x = nt - 0.5
        ax.plot([nt-0.5, nt-0.5], [i-0.5, i+0.5], color=highlight_color, linewidth=linewidth)

# 图例（增加环形连接说明）
legend_patches = [
    mpatches.Patch(color='#FF6B6B', label='FRONT'),
    mpatches.Patch(color='#98FB98', label='PENULT'),
    mpatches.Patch(color='#4ECDC4', label='BEHIND'),
    mpatches.Patch(color='#FFE66D', label='MIDDLE'),
    mpatches.Patch(color=highlight_color, label='TIE'),
]
# 因两个图例项颜色相同，可以合并显示，但为了清晰，单独说明
ax.legend(handles=legend_patches, loc='upper left', bbox_to_anchor=(1.05, 1))

ax.set_title('BLOCKS MAP')
plt.tight_layout()
plt.show()

# 存储相邻边信息
# 方案1：列表，每个元素为 ((行1,列1), (行2,列2), 方向)
edges_list = []

# 1. 普通四邻域：右邻、下邻（避免重复）
# 右邻
for i in range(nl):
    for j in range(nt-1):
        if block[i, j] and block[i, j+1]:
            edges_list.append(((i, j), (i, j+1), 'right'))
# 下邻
for i in range(nl-1):
    for j in range(nt):
        if block[i, j] and block[i+1, j]:
            edges_list.append(((i, j), (i+1, j), 'down'))

# 2. 行方向环形连接（首尾格子）
for i in range(nl):
    if block[i, 0] and block[i, -1]:
        edges_list.append(((i, 0), (i, nt-1), 'circular'))

# 方案2：字典，键为 (行1,列1,行2,列2) 规范化，值为方向
edges_dict = {}
for (c1, c2, d) in edges_list:
    # 规范化，使较小行号或列号的格子在前（环形边特殊处理）
    if d == 'circular':
        key = (c1[0], c1[1], c2[0], c2[1])
    else:
        # 普通邻边，确保顺序统一（例如按行优先，若同行则按列序）
        if c1[0] < c2[0] or (c1[0] == c2[0] and c1[1] < c2[1]):
            key = (c1[0], c1[1], c2[0], c2[1])
        else:
            key = (c2[0], c2[1], c1[0], c1[1])
    edges_dict[key] = d

# 输出结果
print("=" * 50)
print("所有相邻边信息（列表形式）")
print("=" * 50)
for idx, (c1, c2, d) in enumerate(edges_list, 1):
    print(f"{idx:3}. 格子({c1[0]+1},{c1[1]+1}) ↔ 格子({c2[0]+1},{c2[1]+1})  [{d}]")

print("\n" + "=" * 50)
print("所有相邻边信息（字典形式，规范化键）")
print("=" * 50)
for key, d in edges_dict.items():
    r1, c1, r2, c2 = key
    print(f"({r1+1},{c1+1}) ↔ ({r2+1},{c2+1})  [{d}]")