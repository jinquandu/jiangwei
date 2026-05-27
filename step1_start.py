import requests
import time
from datetime import datetime
from pathlib import Path
import pandas as pd

from config import DOTA_REPLAY_DIR, MATCH_DATE_THRESHOLD, TEAM_LIST_CSV, URL_DIR, ensure_runtime_dirs

def get_match_list(team_id):

    url = f"https://api.opendota.com/api/teams/{team_id}/matches"
    
    # 计算 2 个月前的时间戳 (约 60 天)
    # 注意：OpenDota 使用 Unix 时间戳 (秒)

    print(f"正在获取战队 {team_id} 的比赛数据...")
    time.sleep(1)
    
    response = requests.get(url)

    res_matches = []
    
    if response.status_code == 200:
        matches = response.json()
    
        # 4. 打印详细信息
        for match in matches:
            
            match_id = match['match_id']
            start_time = match['start_time']
            dt = datetime.fromtimestamp(start_time)
            date_only = dt.strftime("%Y%m%d")
            if date_only >= MATCH_DATE_THRESHOLD:
                res_matches.append((match["match_id"], match["start_time"]))

    return res_matches

def download_replay(root_dir: Path, team_name: str, dt: str, match_id):
    # 1. 获取比赛元数据
    api_url = f"https://api.opendota.com/api/matches/{match_id}"
    
    # print(f"正在查询比赛 {match_id} 的录像信息...")
    response = requests.get(api_url)
    
    if response.status_code != 200:
        print("❌ 无法获取比赛信息，请检查比赛 ID 是否正确。")
        return

    data = response.json()
    
    # 2. 提取 replay_url
    # 注意：不是所有比赛都有录像，特别是很久以前的比赛或隐私比赛
    replay_url = data.get('replay_url')
    
    if not replay_url:
        print("⚠️ 该比赛没有可用的录像链接（可能已过期或不存在）。")
        return

    replay_dir_path = root_dir / team_name / dt

    replay_dir_path.mkdir(parents=True, exist_ok=True)
    file_name = replay_dir_path / f"{match_id}.dem"

    if not file_name.exists():
        print(f"✅ 找到录像链接，准备下载...{file_name}")
        
        try:
            # stream=True 非常重要，用于大文件下载
            with requests.get(replay_url, stream=True) as r:
                r.raise_for_status()
                
                # 获取文件总大小 (MB)
                total_size = int(r.headers.get('content-length', 0)) / (1024 * 1024)

                return (str(replay_dir_path) + "/", replay_url, total_size, "toDo", match_id)
                # print(f"📥 文件大小约为: {total_size:.2f} MB")
                
                # with open(file_name, 'wb') as f:
                #     downloaded = 0
                #     for chunk in r.iter_content(chunk_size=8192):
                #         f.write(chunk)
    
            print(f"🎉 下载完成！文件已保存为: {file_name}")
            print("💡 提示：将文件放入 Dota 2 的 'replays' 文件夹即可观看。")
            
        except Exception as e:
            print(f"❌ 下载过程中出错: {e}")
    else:
        return (str(replay_dir_path) + "/", replay_url, -1, "Done", match_id)
    return ("", "", -1, "", "")



def run_step1() -> None:
    ensure_runtime_dirs()
    df_team = pd.read_csv(TEAM_LIST_CSV, names=["team_id", "team_name", "dt"])
    for _, item_team in df_team.iterrows():
        team_id = item_team["team_id"]
        team_name = item_team["team_name"]
        replay_team_path = URL_DIR / f"{team_name}_replay_url.csv"

        try:
            if not replay_team_path.exists() and len(str(team_name)) > 0:
                time.sleep(1)
                w_list = []
                team_match = get_match_list(team_id)
                for item_match in team_match:
                    match_id = item_match[0]
                    timestamp = item_match[1]
                    dt = datetime.fromtimestamp(timestamp)
                    date_only = dt.strftime("%Y%m%d")

                    w_list.append(download_replay(DOTA_REPLAY_DIR, team_name, date_only, match_id))

                pd.DataFrame(
                    w_list,
                    columns=["replay_dir_path", "replay_url", "size", "status", "match_id"],
                ).to_csv(replay_team_path)
            else:
                df_team_match = pd.read_csv(replay_team_path)
                match_id_dict = {}
                w_list = []
                cnt = 0
                for _id in df_team_match["match_id"].to_list():
                    match_id_dict[_id] = 1
                    cnt += 1

                if cnt > 0:
                    team_match = get_match_list(team_id)
                    for item_match in team_match:
                        match_id = item_match[0]
                        timestamp = item_match[1]
                        dt = datetime.fromtimestamp(timestamp)
                        date_only = dt.strftime("%Y%m%d")

                        if match_id not in match_id_dict:
                            w_list.append(download_replay(DOTA_REPLAY_DIR, team_name, date_only, match_id))

                    df_concat = pd.DataFrame(
                        w_list,
                        columns=["replay_dir_path", "replay_url", "size", "status", "match_id"],
                    )
                    pd.concat([df_team_match, df_concat], ignore_index=True).to_csv(replay_team_path)
        except Exception:
            print(f"{team_name} error!!!!!")


def main() -> None:
    run_step1()


if __name__ == "__main__":
    main()
