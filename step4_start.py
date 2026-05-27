import pickle
import multiprocessing
from pathlib import Path
import warnings
import pandas as pd

warnings.filterwarnings("ignore")


BASE_DIR = Path(__file__).resolve().parent
FEA_DIR = BASE_DIR / "fea"
CSV_DIR = BASE_DIR / "csv"
STEP4_WORKERS = max(1, (multiprocessing.cpu_count() or 1) - 1)


def fea_to_dataframe(path: Path) -> pd.DataFrame:
    with open(path, "rb") as f:
        feature = pickle.load(f)

    one_row_list = []
    for tick_loc in feature:
        one_tick_feature = feature[tick_loc]
        if "player_feature" in one_tick_feature and "label" in one_tick_feature and "game_feature" in one_tick_feature:
            # player_feature
            one_row_fea_df = one_tick_feature["player_feature"].values.reshape(1, -1)
            one_row_fea_df = pd.DataFrame(one_row_fea_df)

            # game_feature
            game_feature = one_tick_feature["game_feature"]
            if isinstance(game_feature, pd.DataFrame):
                one_row_game_fea_df = game_feature.reset_index(drop=True)
            elif isinstance(game_feature, pd.Series):
                one_row_game_fea_df = game_feature.to_frame().T.reset_index(drop=True)
            elif isinstance(game_feature, dict):
                one_row_game_fea_df = pd.DataFrame([game_feature])
            else:
                one_row_game_fea_df = pd.DataFrame([[game_feature]], columns=["game_feature"])

            # label
            gold_dict = dict(one_tick_feature["label"][-1])
            gold_dict["winner"] = one_tick_feature["label"][2]
            gold_dict["tick"] = one_tick_feature["label"][0]
            gold_dict["feature_tick"] = one_tick_feature["label"][1]
            one_row_label_df = pd.DataFrame([gold_dict])

            # concat
            one_row = pd.concat([one_row_fea_df, one_row_game_fea_df, one_row_label_df], axis=1)
            one_row_list.append(one_row)

    if not one_row_list:
        return pd.DataFrame()

    return pd.concat(one_row_list, ignore_index=True)


def process_one_fea(fea_path_str: str) -> tuple[str, str, int]:
    """Return (status, message, rows). status in {'ok','skip','fail'}"""
    fea_path = Path(fea_path_str)
    try:
        result = fea_to_dataframe(fea_path)
        if result.empty:
            return "skip", f"[SKIP] {fea_path.name}: no valid player_feature rows", 0

        out_path = CSV_DIR / f"{fea_path.name}.csv"
        result.to_csv(out_path, index=False)
        return "ok", f"[OK] {fea_path.name} -> {out_path.name} ({len(result)} rows)", len(result)
    except Exception as exc:
        return "fail", f"[FAIL] {fea_path.name}: {exc}", 0


def run_step4() -> None:
    CSV_DIR.mkdir(parents=True, exist_ok=True)

    fea_files = sorted(FEA_DIR.glob("*.fea"))
    if not fea_files:
        print(f"No .fea files found in {FEA_DIR}")
        return

    print(f"Start step4: files={len(fea_files)}, workers={STEP4_WORKERS}")

    success = 0
    failed = 0
    skipped = 0
    total_rows = 0

    with multiprocessing.Pool(STEP4_WORKERS) as pool:
        for status, message, rows in pool.imap_unordered(process_one_fea, [str(p) for p in fea_files]):
            print(message)
            if status == "ok":
                success += 1
                total_rows += rows
            elif status == "skip":
                skipped += 1
            else:
                failed += 1

    print(
        f"Done. total={len(fea_files)}, success={success}, skipped={skipped}, failed={failed}, rows={total_rows}"
    )


def main() -> None:
    run_step4()


if __name__ == "__main__":
    main()