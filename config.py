from pathlib import Path

# Project root
BASE_DIR = Path(__file__).resolve().parent

# Data paths
TEAM_LIST_CSV = BASE_DIR / "team_list.csv"
TEAM_REPLAY_DICT_PKL = BASE_DIR / "team_replay_dict.plk"
ITEM_DICT_PKL = BASE_DIR / "item_dict.pkl"

# Directory layout
URL_DIR = BASE_DIR / "url_dir"
DOTA_REPLAY_DIR = BASE_DIR / "dota_replay"
REPLAY_DIR = BASE_DIR / "replay"
DECOMPRESS_DIR = BASE_DIR / "decompress"
MATCH_DIR = BASE_DIR / "match"
FEATURE_DIR = BASE_DIR / "fea"
CSV_DIR = BASE_DIR / "csv"
MODEL_DIR = BASE_DIR / "model"

# Runtime config
STEP2_WORKERS = 3
STEP3_WORKERS = 6

# Business config
MATCH_DATE_THRESHOLD = "20260201"


def ensure_runtime_dirs() -> None:
    for p in [
        URL_DIR,
        DOTA_REPLAY_DIR,
        REPLAY_DIR,
        DECOMPRESS_DIR,
        MATCH_DIR,
        FEATURE_DIR,
        CSV_DIR,
        MODEL_DIR,
    ]:
        p.mkdir(parents=True, exist_ok=True)
