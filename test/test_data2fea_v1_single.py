from __future__ import annotations

import argparse
import pickle
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import MATCH_DIR,FEATURE_DIR
from step3_start import data2fea_v1


def main() -> None:

    replay_id = "8743439271_1066984467"
    match_path = MATCH_DIR / f"{replay_id}.mad" 
    feature_path =  FEATURE_DIR / f"{replay_id}_v1.fea"

    print(f"[TEST] match={match_path}")
    print(f"[TEST] output={feature_path}")
    data2fea_v1(str(match_path), str(feature_path))


if __name__ == "__main__":
    main()
