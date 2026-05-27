import itertools

import pandas as pd


def mapping_hero_to_id(x, hero_dict):
    """根据英雄名查找对应玩家 id，找不到时返回 -1。"""
    if x in hero_dict:
        return hero_dict[x]["player_id"]
    return -1


def get_damage_feature(combat, f_t, start_tick, end_tick, player_id_index=0, hero_dict=None):
    """计算指定玩家在当前时刻前的伤害统计特征，包括总量、早期与最近窗口。"""
    # 只统计伤害类日志
    c = combat[combat["log_type"] == "DAMAGE"].copy()

    # 定义窗口
    c_total = c[c["tick"] <= f_t].copy()
    c_recent = c[(c["tick"] > max(start_tick, f_t - 5 * 1800)) & (c["tick"] <= f_t)].copy()
    c_early = c[
        (c["tick"] >= start_tick) & (c["tick"] <= min(end_tick, start_tick + 5 * 1800))
    ].copy()

    # 辅助函数计算特征
    def compute_damage_features(c_filtered, player_id_index, hero_dict):
        """内部辅助函数：对给定过滤日志计算玩家相关的伤害特征。"""
        # 关联玩家ID
        if hero_dict is not None:
            c_filtered["attacker_player_id"] = c_filtered["attacker_name"].apply(
                lambda x: mapping_hero_to_id(x, hero_dict)
            )
            c_filtered["target_player_id"] = c_filtered["target_name"].apply(
                lambda x: mapping_hero_to_id(x, hero_dict)
            )
        else:
            c_filtered["attacker_player_id"] = -1
            c_filtered["target_player_id"] = -1

        attacker_mask = c_filtered["attacker_player_id"] == player_id_index
        target_mask = c_filtered["target_player_id"] == player_id_index

        damage_features_dict = {
            "damage_from_hero": c_filtered[
                attacker_mask & c_filtered["attacker_is_hero"]
            ]["value"].sum(),
            "damage_from_nonhero": c_filtered[
                attacker_mask & ~c_filtered["attacker_is_hero"]
            ]["value"].sum(),
            "damage_to_nonhero": c_filtered[target_mask & ~c_filtered["target_is_hero"]][
                "value"
            ].sum(),
            "damage_to_hero": c_filtered[target_mask & c_filtered["target_is_hero"]][
                "value"
            ].sum(),
            "damage_from_illusion": c_filtered[
                attacker_mask & c_filtered["attacker_is_illusion"]
            ]["value"].sum(),
            "damage_from_nonillusion": c_filtered[
                attacker_mask & ~c_filtered["attacker_is_illusion"]
            ]["value"].sum(),
            "damage_to_illusion": c_filtered[target_mask & c_filtered["target_is_illusion"]][
                "value"
            ].sum(),
            "damage_to_nonillusion": c_filtered[
                target_mask & ~c_filtered["target_is_illusion"]
            ]["value"].sum(),
            "damage_attacker": c_filtered[attacker_mask]["value"].sum(),
            "damage_taken": c_filtered[target_mask]["value"].sum(),
        }

        # 生成所有 16 种组合
        for ah, th, ai, ti in itertools.product([True, False], repeat=4):
            mask = (
                (c_filtered["attacker_player_id"] == player_id_index)
                & (c_filtered["attacker_is_hero"] == ah)
                & (c_filtered["target_is_hero"] == th)
                & (c_filtered["attacker_is_illusion"] == ai)
                & (c_filtered["target_is_illusion"] == ti)
            )
            key = (
                f"damage_{'h' if ah else 'nh'}_{'h' if th else 'nh'}_"
                f"{'i' if ai else 'ni'}_{'i' if ti else 'ni'}"
            )
            damage_features_dict[key] = c_filtered[mask]["value"].sum()

        return damage_features_dict

    # 计算三个窗口的特征
    features_total = compute_damage_features(c_total, player_id_index, hero_dict)
    features_recent = compute_damage_features(c_recent, player_id_index, hero_dict)
    features_early = compute_damage_features(c_early, player_id_index, hero_dict)

    # 合并为一个 dict，添加后缀
    combined_dict = {}
    for k, v in features_total.items():
        combined_dict[k + "_total"] = [v]
    for k, v in features_recent.items():
        combined_dict[k + "_recent"] = [v]
    for k, v in features_early.items():
        combined_dict[k + "_early"] = [v]

    damage_features = pd.DataFrame(combined_dict)

    return damage_features
