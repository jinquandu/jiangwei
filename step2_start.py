import pickle
from pathlib import Path
import multiprocessing

from config import REPLAY_DIR, STEP2_WORKERS, TEAM_REPLAY_DICT_PKL, ensure_runtime_dirs
from processing.replay2data import onereplay2data

# replay_dict = {}
# ct = 0
# team_cnt = 0
# error_ct = 0
# directory = "url_dir/"
# for f in os.listdir(directory):
#     df_match_list = pd.read_csv(directory+f)
#     if df_match_list["match_id"].count() > 0:
#         team_cnt += 1
#         for index,item in df_match_list.iterrows():
#             ct+=1
#             try:
#                 team_name = item["replay_dir_path"].split("/")[1]
#                 date = item["replay_dir_path"].split("/")[2]
#                 replay_url = item["replay_url"]
#                 match_id = item["match_id"]
#                 size = int(item["size"])
#                 if match_id not in replay_dict:
#                     replay_dict[match_id] = {}
#                     replay_dict[match_id]["url"] = replay_url
#                     replay_dict[match_id]["size"] = size
#                     replay_dict[match_id]["date"] = date
#                     replay_dict[match_id]["team"] = team_name
#                 else:
#                     replay_dict[match_id]["team"] += "@pk@"+team_name
#             except:
#                 error_ct+=1

# all_size = 0
# for key in replay_dict:
#     all_size += replay_dict[key]["size"]

# print(f"replay num:{len(replay_dict)}")
# print(f"team cnt:{team_cnt}")
# print(f"all Size:{all_size}M")

def load_replay_dict() -> dict:
    with open(TEAM_REPLAY_DICT_PKL, "rb") as f:
        return pickle.load(f)


def run_step2() -> None:
    ensure_runtime_dirs()
    replay_dict = load_replay_dict()

    with multiprocessing.Pool(STEP2_WORKERS) as pool:
        for key in replay_dict:
            replay_url = replay_dict[key]["url"]
            replay_name = replay_url.split("/")[-1]
            replay_file = REPLAY_DIR / replay_name
            match_id = str(key)
            if not replay_file.exists():
                try:
                    pool.apply_async(onereplay2data, (REPLAY_DIR, replay_url, match_id))
                except ValueError as e:
                    print(f"任务 {match_id} 出错: {e}")

        pool.close()
        pool.join()


def main() -> None:
    run_step2()


if __name__ == "__main__":
    main()
    


        