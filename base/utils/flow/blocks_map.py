from pprint import pprint

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches


def draw_map(block):
    """
    根据布尔矩阵 block 绘制 blocks 地图。
    参数:
        block: np.ndarray, 布尔矩阵，True 表示该位置有块
    """
    nl, nt = block.shape

    # 数值矩阵用于颜色
    data = np.zeros_like(block, dtype=int)
    data[0, block[0, :]] = 1
    data[-2, block[-2, :]] = 2
    data[-1, block[-1, :]] = 3
    for i in range(1, nl - 2):
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
    ax.set_xticklabels(range(1, nt + 1))
    ax.set_yticklabels(range(1, nl + 1))

    # 格子边框（黑色网格线）
    ax.set_xticks(np.arange(-0.5, nt, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, nl, 1), minor=True)
    ax.grid(which='minor', color='black', linewidth=0.5, linestyle='-')

    # 在每个 True 格子中心加坐标标签（使用 .format 代替 f-string）
    for i in range(nl):
        for j in range(nt):
            if data[i, j] != 0:
                ax.text(j, i, '({}-{})'.format(i, j), ha='center', va='center', color='black', fontsize=8)

    # 高亮相邻 True 格子之间的共享边
    highlight_color = 'red'
    linewidth = 2.5

    # 向右检查（垂直边）
    for i in range(nl):
        for j in range(nt - 1):
            if block[i, j] and block[i, j + 1]:
                ax.plot([j + 0.5, j + 0.5], [i - 0.5, i + 0.5], color=highlight_color, linewidth=linewidth)

    # 向下检查（水平边）
    for i in range(nl - 1):
        for j in range(nt):
            if block[i, j] and block[i + 1, j]:
                ax.plot([j - 0.5, j + 0.5], [i + 0.5, i + 0.5], color=highlight_color, linewidth=linewidth)

    # 行方向环状接触：检查每行的第一个和最后一个格子
    for i in range(nl):
        if block[i, 0] and block[i, -1]:
            ax.plot([-0.5, -0.5], [i - 0.5, i + 0.5], color=highlight_color, linewidth=linewidth)      # 左边界
            ax.plot([nt - 0.5, nt - 0.5], [i - 0.5, i + 0.5], color=highlight_color, linewidth=linewidth) # 右边界

    # 图例
    legend_patches = [
        mpatches.Patch(color='#FF6B6B', label='FRONT'),
        mpatches.Patch(color='#98FB98', label='PENULT'),
        mpatches.Patch(color='#4ECDC4', label='BEHIND'),
        mpatches.Patch(color='#FFE66D', label='MIDDLE'),
        mpatches.Patch(color=highlight_color, label='TIE'),
    ]
    ax.legend(handles=legend_patches, loc='upper left', bbox_to_anchor=(1.05, 1))

    ax.set_title('BLOCKS MAP')
    plt.tight_layout()
    plt.show()


def output_edges_dict(block):
    """
    根据 block 矩阵计算相邻（包括环形相邻）的格子对，并输出字典。
    参数:
        block: np.ndarray, 布尔矩阵，True 表示有块
    """
    nl, nt = block.shape
    edges_list = []

    # 右邻
    for i in range(nl):
        for j in range(nt - 1):
            if block[i, j] and block[i, j + 1]:
                edges_list.append(((i, j), (i, j + 1), 'right'))

    # 下邻
    for i in range(nl - 1):
        for j in range(nt):
            if block[i, j] and block[i + 1, j]:
                edges_list.append(((i, j), (i + 1, j), 'down'))

    # 环形连接（行方向首尾）
    for i in range(nl):
        if block[i, 0] and block[i, -1]:
            edges_list.append(((i, 0), (i, nt - 1), 'circular'))

    # 规范化并存入字典
    edges_dict = {}
    for (c1, c2, d) in edges_list:
        if d == 'circular':
            key = (c1[0], c1[1], c2[0], c2[1])
        else:
            # 普通邻边，确保顺序统一（按行优先，同行则按列序）
            if c1[0] < c2[0] or (c1[0] == c2[0] and c1[1] < c2[1]):
                key = (c1[0], c1[1], c2[0], c2[1])
            else:
                key = (c2[0], c2[1], c1[0], c1[1])
        edges_dict[key] = d

    # 打印输出（使用 .format 代替 f-string）
    for key, d in edges_dict.items():
        r1, c1, r2, c2 = key
        print("({},{}) ↔ ({},{})  [{}]".format(r1 + 1, c1 + 1, r2 + 1, c2 + 1, d))

    return edges_dict


if __name__ == "__main__":
    # 生成 block 矩阵（与原代码逻辑一致）
    nl, nt = 12, 9
    block = np.zeros((nl, nt), dtype=bool)
    block[:, 0] = True
    block[:, 1] = True
    block[:, 8] = True

    # draw_map(block)          # 绘图
    edges_dict = output_edges_dict(block) # 输出字典
    from pprint import pprint
    pprint(edges_dict) # 美化打印字典