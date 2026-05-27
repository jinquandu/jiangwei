"""
功能:
- 从 OpenDota 拉取战队列表，筛选活跃战队，生成 team_list.csv。

输入:
- OpenDota /teams 接口返回的战队数据
- 脚本内置时间阈值（当前逻辑为 20260201 之后）

输出:
- team_list.csv（每行: team_id,team_name,last_match_date）
"""

import requests
import time
from datetime import datetime, timedelta
import os

def get_teams_list():
    # 1. 定义 API 接口地址
    # 获取战队列表的接口是 /teams
    url = "https://api.opendota.com/api/teams"
    
    team_list = []
    
    # 2. 发送 GET 请求
    response = requests.get(url)
    
    # 3. 检查请求状态
    if response.status_code == 200:
        teams = response.json()
        
        print(f"✅ 成功获取到 {len(teams)} 支战队的数据！\n")
        
        # 4. 遍历并打印关键信息
        for team in teams:
            team_id = team.get('team_id')
            name = team.get('name')
            last_match_dt = datetime.fromtimestamp(team.get('last_match_time')).strftime("%Y%m%d")
    
            team_list.append((team_id,name,last_match_dt))
    
    else:
        print(f"❌ 请求失败，状态码: {response.status_code}")
    
    return team_list


team_list = get_teams_list()
if len(team_list) > 100:
    f = open("team_list.csv","w")
    for item in team_list:
        if item[2] > "20260201":
            f.write(str(item[0])+","+item[1]+","+item[2]+"\n")
    f.close()