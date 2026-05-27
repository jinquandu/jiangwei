"""
功能:
- 汇总 url_dir 下各战队 replay 清单，按 match_id 去重并输出 team_replay_dict.plk。

输入:
- url_dir/*.csv（包含 replay_url、match_id、size、replay_dir_path 等字段）

输出:
- team_replay_dict.plk（键为 match_id，值包含 url/size/date/team）
- 控制台统计（replay 数量、战队数量、总大小）
"""

# 万一录像重复呢？
import os
import pandas as pd
import pickle
replay_dict = {}
ct = 0
team_cnt = 0
error_ct = 0
directory = "url_dir/"
for f in os.listdir(directory):
    df_match_list = pd.read_csv(directory+f)
    if df_match_list["match_id"].count() > 0:
        team_cnt += 1
        for index,item in df_match_list.iterrows():
            ct+=1
            try:
                team_name = item["replay_dir_path"].split("/")[1]
                date = item["replay_dir_path"].split("/")[2]
                replay_url = item["replay_url"]
                match_id = item["match_id"]
                size = int(item["size"])
                if match_id not in replay_dict:
                    replay_dict[match_id] = {}
                    replay_dict[match_id]["url"] = replay_url
                    replay_dict[match_id]["size"] = size
                    replay_dict[match_id]["date"] = date
                    replay_dict[match_id]["team"] = team_name
                else:
                    replay_dict[match_id]["team"] += "@pk@"+team_name
            except:
                error_ct+=1

all_size = 0
for key in replay_dict:
    all_size += replay_dict[key]["size"]

print(f"replay num:{len(replay_dict)}")
print(f"team cnt:{team_cnt}")
print(f"all Size:{all_size}M")

# 保存到文件
with open("team_replay_dict.plk", 'wb') as f:
    pickle.dump(replay_dict, f)