import pickle
import time
import multiprocessing
import warnings
from pathlib import Path

from config import FEATURE_DIR, MATCH_DIR, STEP3_WORKERS, ensure_runtime_dirs
from processing.data2feature import get_all_feature
from processing.data2label import get_label


def data2fea_v1(match_path,feature_path):

    
    with open(match_path, 'rb') as f:
        match_info_pickle = pickle.load(f)
    
    match = match_info_pickle["match"]
    dfs = match_info_pickle["dfs"]
    inventory = match_info_pickle["inventory"]
    herostatus = match_info_pickle["hero_status"]
    
    feature_dict = {}
    label_tick = get_label(match,dfs)
    print(match_path, len(label_tick))
    start_time = time.time()
    for label_item in label_tick:
        
        f_t = label_item[1]
        #print(f_t,time.time())
        try:
            df_player_feature,df_game_feature = get_all_feature(match, dfs, inventory,herostatus,f_t)
        
            feature_dict[f_t] = {}
            feature_dict[f_t]["label"] = label_item
            feature_dict[f_t]["player_feature"] = df_player_feature
            feature_dict[f_t]["game_feature"] = df_game_feature
        except Exception:
            print(label_item)
            feature_dict[f_t] = {}
            feature_dict[f_t]["error"] = 1
            feature_dict[f_t]["label"] = label_item
    
    end_time = time.time()
    print(match_path, end_time - start_time)
    
    # 保存到文件
    with open(feature_path, 'wb') as f:
        pickle.dump(feature_dict, f)
        
warnings.filterwarnings("ignore")

def run_step3() -> None:
    ensure_runtime_dirs()
    with multiprocessing.Pool(STEP3_WORKERS) as pool:
        f_list = [f for f in MATCH_DIR.iterdir() if f.suffix == ".mad"]
        total_tasks = len(f_list)
        skipped_tasks = 0
        triggered_tasks = 0
        for match_path in f_list:
            feature_path = FEATURE_DIR / f"{match_path.stem}_v1.fea"
            if feature_path.exists():
                skipped_tasks += 1
                # print(f"[SKIP] {feature_path.name} already exists")
            else:
                try:
                    pool.apply_async(data2fea_v1, (str(match_path), str(feature_path)))
                    triggered_tasks += 1
                except ValueError as e:
                    print(f"任务 {match_path.name} 出错: {e}")
        print(f"总任务: {total_tasks}, 已跳过: {skipped_tasks}, 已触发: {triggered_tasks}")

        pool.close()
        pool.join()



def main() -> None:
    run_step3()


if __name__ == "__main__":
    main()
    


        