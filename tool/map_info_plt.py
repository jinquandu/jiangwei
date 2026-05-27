"""
功能:
- 读取 resource 目录中的地图数据并可视化地形、通行点、树木分布。

输入:
- resource/elevationdata_32.json
- resource/gridnavdata.json
- resource/mapdata.json

输出:
- Matplotlib 绘图窗口（地图可视化结果）
"""

import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

RESOURCE_DIR = Path(__file__).resolve().parent.parent / "resource"

# 2. 创建画布
plt.figure(figsize=(20, 16)) # 设置图片大小

file_name = RESOURCE_DIR / "elevationdata_32.json"
import json

# 使用 with open 语句自动管理文件的打开和关闭
# 强烈建议指定 encoding='utf-8'，防止中文乱码
with open(file_name, 'r', encoding='utf-8') as f:
    # json.load() 会直接将文件内容转化为 Python 字典
    python_data = json.load(f)

# 1. 准备网格数据
# 在 -5 到 5 的范围内生成 100 个点
size = 519
x = np.linspace(-8000, 8000, size)
y = np.linspace(-8000, 8000, size)
# 生成二维网格坐标
min_value = 1
max_value = 1
X, Y = np.meshgrid(x, y)
Z = python_data["data"]
for i in range(0,len(Z)):
    for j in range(0,len(Z[0])):
        if Z[i][j] == -128:
            Z[i][j] = -2
        if min_value > Z[i][j]:
            min_value = Z[i][j]
        if max_value < Z[i][j]:
            max_value = Z[i][j]
            
# 第一步：绘制带填充颜色的等高线 (contourf)
# cmap='coolwarm' 指定了蓝-白-红的冷暖色调，levels=15 表示将高度分为15个层级
contour_fill = plt.contourf(X, Y, Z, cmap='coolwarm', alpha=0.3)



file_name = RESOURCE_DIR / "gridnavdata.json"


    
f=open(file_name,"r")
file_str = ""
for line in f.readlines():
    file_str += line
f.close()
import json
gridnavdata = json.loads(file_str)
data = gridnavdata["data"]

y = []
x = []
for item in data:
    y.append(item["y"])
    x.append(item["x"])



plt.scatter(x, y,alpha=0.6, cmap='viridis')

file_name = RESOURCE_DIR / "mapdata.json"

f=open(file_name,"r")
file_str = ""
for line in f.readlines():
    file_str = line
f.close()
import json
mapdata = json.loads(file_str)
tree = mapdata["data"]["ent_dota_tree"]

y = []
x = []
for item in tree:
    y.append(item["y"])
    x.append(item["x"])
plt.scatter(x, y,alpha=0.6, cmap='viridis')


# positions_by_tick = positions[positions["tick"]>35873][positions["tick"]<36873]

# for player_id in range(0,10):
#     df_player_one = positions_by_tick[positions_by_tick["player_id"]==player_id]
    
#     # 假设 x 是时间，y 是数值
#     x = df_player_one["x"]-16000
#     y = df_player_one["y"]-16000
#     plt.scatter(x, y,alpha=0.6, cmap='viridis')

# 4. 添加标签和标题
plt.xlabel('X', fontsize=12)
plt.ylabel('Y', fontsize=12)


# 6. 显示网格
plt.grid(True, linestyle='--', alpha=0.5)

# 7. 显示图表
plt.show()