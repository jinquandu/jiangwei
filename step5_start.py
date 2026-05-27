from __future__ import annotations

from pathlib import Path
import warnings

import pandas as pd
import hashlib
from config import CSV_DIR
import xgboost as xgb
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import matplotlib.pyplot as plt
import seaborn as sns
import joblib

warnings.filterwarnings("ignore")

MERGED_OUTPUT_FILE = Path("merged_data.csv")


def load_and_merge_csv_data(
	csv_dir: Path = CSV_DIR,
	exclude_files: set[str] | None = None,
) -> pd.DataFrame:
	"""Read all CSV files in a directory and merge them into one DataFrame."""
	exclude_files = exclude_files or set()
	csv_files = sorted(
		csv_file for csv_file in csv_dir.glob("*.csv") if csv_file.name not in exclude_files
	)
	if not csv_files:
		raise FileNotFoundError(f"No CSV files found in: {csv_dir}")

	frames: list[pd.DataFrame] = []
	for csv_file in csv_files:
		try:
			df = pd.read_csv(csv_file)
			# Keep source file name for traceability in downstream analysis.
			df["source_file"] = csv_file.name
			frames.append(df)
		except Exception as exc:
			print(f"[SKIP] {csv_file.name}: {exc}")

	if not frames:
		raise ValueError("All CSV files failed to read. No merged result generated.")

	merged_df = pd.concat(frames, ignore_index=True)
	return merged_df


def save_merged_csv(
	merged_df: pd.DataFrame,
	output_path: Path | str = MERGED_OUTPUT_FILE,
) -> Path:
	"""Save merged DataFrame to local CSV file and return the output path."""
	output_path = Path(output_path)
	output_path.parent.mkdir(parents=True, exist_ok=True)
	merged_df.to_csv(output_path, index=False)
	return output_path

def get_columns_info(merged_df: pd.DataFrame) -> str:

    fea_col_file = "/Users/jq/Desktop/jiangwei/feature_colums.txt"
    fea_col_list = []
    f = open(fea_col_file,"r")
    for line in f.readlines():
        fea_col_list.append(line.strip())
    f.close()

    feature_col = []
    info_col = []
    label_col =['target_gold_rate_900','target_gold_diff_1800','target_gold_rate_1800','target_gold_diff_5400','target_gold_rate_5400','target_gold_diff_9000','target_gold_rate_9000','winner']
    for _n in merged_df.columns:
        if _n in fea_col_list or _n.isdigit():
            feature_col.append(_n)
        elif _n not in label_col:
            info_col.append(_n)
        # else:
        #     print(_n)
    return feature_col,info_col,label_col

def split_train_test_by_source_file(
    df: pd.DataFrame,
    test_ratio: float = 0.2,
    seed: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split by source_file group to avoid leakage.
    Same source_file will only appear in one split.
    """
    if "source_file" not in df.columns:
        raise KeyError("Column 'source_file' is required for split.")

    if not (0.0 < test_ratio < 1.0):
        raise ValueError("test_ratio must be between 0 and 1.")

    # Deterministic hash-based split on source_file
    def in_test_group(source_name: str) -> bool:
        key = f"{seed}::{source_name}".encode("utf-8")
        h = int(hashlib.md5(key).hexdigest(), 16) % 10000
        return h < int(test_ratio * 10000)

    source_flag = (
        df["source_file"]
        .astype(str)
        .drop_duplicates()
        .to_frame(name="source_file")
    )
    source_flag["is_test"] = source_flag["source_file"].map(in_test_group)

    # 防止极端情况下某一侧为空
    if source_flag["is_test"].sum() == 0:
        source_flag.loc[source_flag.index[:1], "is_test"] = True
    if source_flag["is_test"].sum() == len(source_flag):
        source_flag.loc[source_flag.index[:1], "is_test"] = False

    test_sources = set(source_flag.loc[source_flag["is_test"], "source_file"])
    train_sources = set(source_flag.loc[~source_flag["is_test"], "source_file"])

    train_df = df[df["source_file"].isin(train_sources)].reset_index(drop=True)
    test_df = df[df["source_file"].isin(test_sources)].reset_index(drop=True)

    return train_df, test_df

def train_model(train_df, test_df, feature_col ,label_target):
    X_train = train_df[feature_col]
    y_train = train_df[label_target]

    X_test = test_df[feature_col]
    y_test = test_df[label_target]

    # 3. 初始化 XGBoost 回归器
    model = xgb.XGBRegressor(
        n_estimators=500,         # 最大迭代次数（树的个数）
        max_depth=3,              # 树的最大深度
        learning_rate=0.05,       # 学习率（步长）
        subsample=0.8,            # 样本采样比例（防止过拟合）
        colsample_bytree=0.8,     # 特征采样比例
        eval_metric='rmse',       # 监控指标：均方根误差
        n_jobs=-1,
        enable_categorical=True
    )

    # 4. 训练模型
    model.fit(
        X_train, y_train,
        eval_set=[(X_train, y_train),(X_test, y_test)],  # 传入测试集作为验证集来监控表现
        verbose=True                  # 打印训练日志
    )

    # 5. 模型存储
    joblib.dump(model, "model/xgb_model_"+label_target+".joblib")

    return model

def main() -> None:
    train_cache_path = Path("train_data.csv")
    if train_cache_path.exists() == False:
        merged_df = load_and_merge_csv_data(exclude_files={MERGED_OUTPUT_FILE.name})
        output_path = save_merged_csv(merged_df,train_cache_path)
        print(f"Merged rows: {len(merged_df)}")
        print(f"Merged cols: {merged_df.shape[1]}")
        print(f"Saved merged csv: {output_path.resolve()}")
    else:
        merged_df = pd.read_csv(train_cache_path)

    # 1. 找出所有 object 类型的列，并将其转换为 category 类型
    for col in merged_df.select_dtypes(include=['object']).columns:
        merged_df[col] = merged_df[col].astype('category')
    feature_col,info_col,label_col = get_columns_info(merged_df)
    train_df, test_df = split_train_test_by_source_file(merged_df)

    for _label  in label_col:
        if _label != "winner":
            print(f"Training model for label: {_label}")
            model = train_model(train_df, test_df, feature_col ,_label)
        else:
            # 过滤掉winner列中非draw和radiant的异常值
            train_df_filtered = train_df[train_df["winner"].isin(["draw", "radiant"])]
            test_df_filtered = test_df[test_df["winner"].isin(["draw", "radiant"])]
            # 将winner列转换为二分类标签：radiant=1, draw=0
            train_df_filtered["winner"] = train_df_filtered["winner"].map({"radiant": 1, "draw": 0})
            test_df_filtered["winner"] = test_df_filtered["winner"].map({"radiant": 1, "draw": 0})
            print(f"Training model for label: {_label}")
            model = train_model(train_df_filtered, test_df_filtered, feature_col ,_label)

if __name__ == "__main__":
	main()
