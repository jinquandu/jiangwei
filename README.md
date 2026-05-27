# Jiangwei Dota Replay Pipeline

## 1. 项目简介

这个项目用于构建 Dota2 比赛数据训练流水线，核心目标是：

- 从 OpenDota 拉取战队比赛信息与 replay 链接
- 下载并解析 replay，产出结构化中间数据
- 计算玩家与全局特征，生成监督学习标签
- 将特征与标签拼接为 CSV 数据集
- 使用 XGBoost 训练回归模型（目标列为 target_gold_rate_900）

项目采用 step1 到 step5 的顺序式处理，便于分阶段执行与排错。

## 2. 目录结构

- config.py
  - 全局配置中心，统一管理目录、并发参数和业务阈值

- step1_start.py
  - 采集战队比赛列表，生成每个战队的 replay URL 清单

- step2_start.py
  - 读取 team_replay_dict.plk，下载并解析 replay，输出 match 中间文件

- step3_start.py
  - 从 match 生成 fea 特征文件（已支持存在即跳过）

- step4_start.py
  - 将 fea 目录中的全部文件转换为 csv 数据

- step5_start.py
  - 从 csv 目录读取数据并训练 XGBoost 回归模型

- pipeline/
  - step1 到 step5 的包装入口，便于统一调度

- processing/
  - 核心处理模块（原根目录 data2feature.py、data2label.py、replay2data.py 已迁入）

- feature/
  - 特征工程细分模块（farm、damage、item、ward、position、info）

- tool/
  - 辅助脚本（例如战队列表处理、清理空 CSV 等）

- url_dir/
  - 战队 replay URL 文件

- replay/
  - 下载后的 .dem.bz2 文件

- decompress/
  - 解压后的 .dem 文件

- match/
  - replay 解析后中间数据（.mad）

- fea/
  - 特征与标签的 pickle 文件（.fea）

- csv/
  - 训练输入数据（特征与标签拼接）

- model/
  - 训练产物（模型文件与指标文件）

## 3. 数据流

Step1: team_list.csv -> url_dir/*.csv

Step2: team_replay_dict.plk + URL -> replay/ + decompress/ + match/*.mad

Step3: match/*.mad -> fea/*.fea

Step4: fea/*.fea -> csv/*.csv

Step5: csv/*.csv -> model/xgb_target_gold_rate_900.json

## 4. 环境依赖

建议 Python 版本：3.10 或以上。

基础依赖：

- pandas
- numpy
- requests
- xgboost
- gem（项目中用于 replay 解析）

安装示例：

python3 -m pip install pandas numpy requests xgboost

如果你使用 conda，请确认运行脚本时使用的是已安装依赖的同一个环境。

## 5. 配置说明

配置文件在 config.py，常用项：

- STEP2_WORKERS
- STEP3_WORKERS
- MATCH_DATE_THRESHOLD
- FEATURE_DIR、CSV_DIR、MODEL_DIR 等目录常量

首次运行前会自动创建必要目录（由 ensure_runtime_dirs 统一处理）。

## 6. 运行方式

按顺序执行：

1. python step1_start.py
2. python step2_start.py
3. python step3_start.py
4. python step4_start.py
5. python step5_start.py

也可以使用 pipeline 包装入口：

1. python pipeline/step1.py
2. python pipeline/step2.py
3. python pipeline/step3.py
4. python pipeline/step5.py

说明：step4 当前只在根目录提供入口脚本。

## 7. 训练数据约定（Step5）

step5_start.py 默认约定：

- 特征列："0" 到 "2689"
- 目标列：target_gold_rate_900

脚本会自动读取 csv 目录下所有文件，拼接后训练，并输出：

- model/xgb_target_gold_rate_900.json
- model/xgb_target_gold_rate_900_metrics.txt

## 8. 增量与跳过策略

- step3_start.py 中，如果目标 fea 文件已经存在，会直接跳过
- step3_start.py 会打印任务统计日志：
  - total: 总候选任务数
  - triggered: 实际提交处理的任务数
  - skipped: 因已存在输出而跳过的任务数

## 9. 常见问题

1) 运行 step5 报错 ModuleNotFoundError

原因：当前 Python 环境缺少 pandas、numpy、xgboost。

处理：安装依赖并确认 python3 指向同一环境。

2) step3 处理速度慢

可适当提高 STEP3_WORKERS，但需要结合 CPU 与内存资源。

3) 某些 replay 无法下载或解析

项目内已有异常兜底与跳过逻辑，建议观察日志并重跑增量任务。

## 10. 后续建议

- 增加 requirements.txt 或 pyproject.toml，固定依赖版本
- 为 step4、step5 增加参数化入口（目标列、特征范围、输出路径）
- 增加最小单测，覆盖数据列完整性与关键函数输出结构
