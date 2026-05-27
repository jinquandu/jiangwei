# 标签定义
import gem
import os
from gem.parser import ReplayParser
from gem.extractors.players import PlayerExtractor
import pandas as pd
import numpy as np
import pickle


# fight label
# get start_tick,end_tick
def get_gamerange_tick(df_farmFeature):
    """根据玩家采样数据，计算游戏有效区间的起始与结束 tick。"""
    list_t = df_farmFeature["tick"].tolist()
    return list_t[0],list_t[-1]

    
def get_fight_label(match):
    fight_label_res = []
    for item in match.teamfights:
        # item.start_tick 采样点:[10*300,站前取10*30个,战后取10*30个,10*300]
        loc = item.start_tick
        for i in range(1,10):
            
            # +1s:站前取10*30个
            fight_label_res.append([loc,loc - i*30,item.winner])
            
            # -1s:战后取10*30个
            if loc + i*30 < item.end_tick:
                fight_label_res.append([loc,loc + i*30,item.winner])
                
            # 10s:战前谋划
            fight_label_res.append([loc,loc - i*300,item.winner])
            
            # 10s:战后收益
            if loc + i*30 < item.end_tick:
                fight_label_res.append([loc,loc + i*300,"None"])

    return fight_label_res

def get_gold_line_by_team(dfs):
    """
    按采样 tick 计算两队经济差。
    返回每个 tick 上天辉与夜魇的当前金币总和、净资产总和，以及
    天辉减夜魇的差值。
    """
    import pandas as pd

    players = dfs.get("players")
    if players is None or players.empty:
        return pd.DataFrame(
            columns=[
                "tick",
                "radiant_gold",
                "dire_gold",
                "gold_diff",
                "radiant_net_worth",
                "dire_net_worth",
                "net_worth_diff",
            ]
        )

    target_col = ["tick","team","player_id","gold","net_worth"]
    players_gold = players[target_col]
    players_gold = players_gold.drop_duplicates()
    team_gold = (
        players_gold.groupby(["tick", "team"], as_index=False)[["gold", "net_worth"]]
        .sum()
        .sort_values(["tick", "team"])
    )

    gold_pivot = team_gold.pivot(index="tick", columns="team", values="gold").fillna(0)
    net_worth_pivot = (
        team_gold.pivot(index="tick", columns="team", values="net_worth").fillna(0)
    )

    result = pd.DataFrame({
        "tick": gold_pivot.index,
        "radiant_gold": gold_pivot.get(2, pd.Series(0, index=gold_pivot.index)).to_numpy(),
        "dire_gold": gold_pivot.get(3, pd.Series(0, index=gold_pivot.index)).to_numpy(),
        "radiant_net_worth": net_worth_pivot.get(2, pd.Series(0, index=net_worth_pivot.index)).to_numpy(),
        "dire_net_worth": net_worth_pivot.get(3, pd.Series(0, index=net_worth_pivot.index)).to_numpy(),
    })

    result["gold_diff"] = result["radiant_gold"] - result["dire_gold"]
    result["gold_rate"] = (result["radiant_gold"]+0.1)/(result["radiant_gold"] + result["dire_gold"]+0.2)
    result["net_worth_diff"] = result["radiant_net_worth"] - result["dire_net_worth"]
    return result.reset_index(drop=True)

def get_gold_tick_random(dfs):
    players   = dfs["players"]
    start_tick, end_tick = get_gamerange_tick(players[players["player_id"] == 0])
    # 从10分钟开始，每30秒取一个tick
    _random_tich_list = []
    _random_tich = start_tick
    while _random_tich < end_tick:
        _random_tich_list.append([_random_tich,_random_tich,"None"])
        _random_tich += + 30*30
    return _random_tich_list

# 计算0.5分钟,1分钟，3分钟，5分钟后的经济差
def get_gold_diff(df_gold_res,target_tick):
    res_gold = {}
    try:
        target_item = df_gold_res[df_gold_res["tick"] <= target_tick].iloc[-1]
        target_diff = float(target_item["gold_diff"])
        target_rate = float(target_item["gold_rate"])
        res_gold["target_gold_diff"] = target_diff
        res_gold["target_gold_rate"] = target_rate
        res_gold["radiant_gold"] = target_item["radiant_gold"]
        res_gold["dire_gold"] = target_item["dire_gold"]
    except:
        res_gold["target_gold_diff"] = 0
        res_gold["target_gold_rate"] = 0.5
        res_gold["radiant_gold"] = 0
        res_gold["dire_gold"] = 0
        target_diff = 0
        target_rate = 0.5
    
    for _left_tick in [30*30,30*60,30*60*3,30*60*5]:
        l_tick = target_tick + _left_tick
        try:
            l_diff = float(df_gold_res[df_gold_res["tick"] <= l_tick].iloc[-1]["gold_diff"])
            l_rate = float(df_gold_res[df_gold_res["tick"] <= l_tick].iloc[-1]["gold_rate"])

            key = "_"+str(_left_tick)
            res_gold["target_gold_diff"+key] = l_diff - target_diff
            res_gold["target_gold_rate"+key] = l_rate - target_rate
        except:
            key = "_"+str(_left_tick)
            res_gold["target_gold_diff"+key] = 0 - target_diff
            res_gold["target_gold_rate"+key] = 0.5 - target_rate

    return res_gold

def get_label(match,dfs):
    fight_label_list = get_fight_label(match)
    gold_label_list = get_gold_tick_random(dfs)
    label_list = fight_label_list + gold_label_list
    
    # 获取所有时刻的经济差
    df_gold_res = get_gold_line_by_team(dfs)
    # 计算1分钟，3分钟，5分钟后的经济差
    
    for i in range(len(label_list)):
        label_list[i].append(get_gold_diff(df_gold_res,label_list[i][0]))

    return label_list