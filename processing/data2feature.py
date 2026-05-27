import pandas as pd
import pickle

from config import ITEM_DICT_PKL

from feature import (
    get_damage_feature,
    get_farm_feature,
    get_gamerange_tick,
    get_info_feature,
    get_item_feature,
    get_position_feature,
    get_ward_feature,
)

def get_hero_mapping(match):
    """从 match 对象中提取玩家与英雄的映射关系，支持 id 和英雄名互转。"""
    player_id_dict = {}
    hero_dict = {}
    player_name_dict = {}
    for player in match.players:
        if player.player_name not in player_name_dict:
            player_name_dict[player.player_name] = {}
        player_name_dict[player.player_name]["player_id"] = player.player_id
        player_name_dict[player.player_name]["hero"] = player.hero_name

        if player.hero_name not in hero_dict:
            hero_dict[player.hero_name] = {}
        hero_dict[player.hero_name]["player_id"] = player.player_id
        hero_dict[player.hero_name]["player_name"] = player.player_name
        
        if player.player_id not in player_id_dict:
            player_id_dict[player.player_id] = {}
        player_id_dict[player.player_id]["hero"] = player.hero_name
        player_id_dict[player.player_id]["player_name"] = player.player_name
        player_id_dict[player.player_id]["team"] = player.team
        player_id_dict[player.player_id]["rank"] = player.gold_t[-1]

    return player_id_dict,hero_dict,player_name_dict




def get_all_feature(match, dfs, inventory, herostatus, f_t):
    """汇总全场玩家的多种特征，目前示例仅计算伤害特征并返回合并结果。"""
    import pandas as pd

    players   = dfs["players"]     # one row per player per sample tick
    positions = dfs["positions"]   # one row per (player, tick) with x/y coords
    combat    = dfs["combat_log"]  # all combat log entries
    wards     = dfs["wards"]       # ward placements

    # 假设所有的玩家tick范围相同，获取第一个玩家的tick范围
    start_tick, end_tick = get_gamerange_tick(players[players["player_id"] == 0])
    player_id_dict, hero_dict, player_name_dict = get_hero_mapping(match)

    # item_loc_dict = get_item_dict(play_ext)
    with open(ITEM_DICT_PKL, "rb") as f:
        item_loc_dict = pickle.load(f)
        
        item_columns = [""]*len(item_loc_dict)
        for key in item_loc_dict:
            item_columns[item_loc_dict[key]] = key

    all_rows = []
    # 遍历全场10名玩家 (player_id 0-9)
    for player_id_index in range(10):
        player_feature_farm = get_farm_feature(dfs, f_t, start_tick, end_tick, player_id_index=player_id_index)
        player_feature_damage = get_damage_feature(
            combat,
            f_t,
            start_tick,
            end_tick,
            player_id_index=player_id_index,
            hero_dict=hero_dict,
        )
        player_feature_item = get_item_feature(
            inventory,
            item_columns,
            f_t,
            start_tick,
            end_tick,
            item_loc_dict,
            player_id_index=player_id_index
        )
        player_feature_position = get_position_feature(positions, f_t, start_tick, end_tick, player_id_index=player_id_index)
        player_feature = pd.concat([player_feature_farm, player_feature_damage, player_feature_item, player_feature_position], axis=1)
        player_feature["player_id"] = player_id_index
        player_feature["player_rank"] = player_id_dict[player_id_index]["rank"]
        player_feature["team"] = player_id_dict[player_id_index]["team"]
        all_rows.append(player_feature)
    # 合并所有玩家的特征行为一个 DataFrame
    import pandas as pd
    if all_rows:
        player_feature = pd.concat(all_rows, axis=0, ignore_index=True)

    # 环境特征
    ward_feature = get_ward_feature(wards,f_t,start_tick, end_tick)
    info_feature = get_info_feature(dfs,f_t,start_tick, end_tick)
    game_feature = pd.concat([ward_feature,info_feature], axis=1)
    return player_feature,game_feature




# import time
# import pickle

# match_path = "/opt/anaconda3/bin/Game/D:/dota_replay/1w Team/20260413/8770130252_330551299.mad"

# # with open(match_path, 'rb') as f:
# #     match_info_pickle = pickle.load(f)


# match = match_info_pickle["match"]
# dfs = match_info_pickle["dfs"]
# inventory = match_info_pickle["inventory"]
# herostatus = match_info_pickle["hero_status"]

# f_t = 25451
# df_player_feature,df_game_feature = get_all_feature(match, dfs, inventory,herostatus,f_t)

# 标签定义
