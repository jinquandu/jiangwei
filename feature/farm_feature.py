import pandas as pd


# get start_tick,end_tick
def get_gamerange_tick(df_farmFeature):
    """根据玩家采样数据，计算游戏有效区间的起始与结束 tick。"""
    list_t = df_farmFeature["tick"].tolist()
    return list_t[0], list_t[-1]


def farm_feature_now(df_farmFeature, f_t, start_tick, end_tick):
    """计算指定时间点的当前农、经济等特征，并归一化为相对于开局的速率。"""
    target_name = ["tick", "lh", "dn", "xp", "gold"]
    df_ff_now1 = df_farmFeature[df_farmFeature["tick"] <= f_t].tail(1)
    feature_name = []
    for _n in target_name:
        if _n != "tick":
            _v_n = "df_ff_now_" + _n + "_v"

            feature_name.append(_n)
            feature_name.append(_v_n)
            df_ff_now1[_v_n] = df_ff_now1[_n] / (df_ff_now1["tick"] - start_tick)

    return df_ff_now1[feature_name]


def farm_feature_log(df_farmFeature, f_t, start_tick, end_tick):
    """提取指定时间点前的早期与最近一段时间的经济、经验与补刀特征。"""
    # 开局5分钟：从start_tick到start_tick + 5*1800
    early_end_tick = min(end_tick, start_tick + 5 * 1800)
    early_df = df_farmFeature[df_farmFeature["tick"] <= early_end_tick]
    if not early_df.empty:
        early_lh = early_df["lh"].iloc[-1]
        early_dn = early_df["dn"].iloc[-1]
        early_xp = early_df["xp"].iloc[-1]
        early_gold = early_df["gold"].iloc[-1]
    else:
        early_lh = 0
        early_dn = 0
        early_xp = 0
        early_gold = 0

    # 最近5分钟：从max(start_tick, f_t - 5*1800)到f_t
    recent_start_tick = max(start_tick, f_t - 5 * 1800)
    recent_end_df = df_farmFeature[df_farmFeature["tick"] <= f_t]
    recent_start_df = df_farmFeature[df_farmFeature["tick"] <= recent_start_tick]

    if not recent_end_df.empty and not recent_start_df.empty:
        recent_lh = recent_end_df["lh"].iloc[-1] - recent_start_df["lh"].iloc[-1]
        recent_dn = recent_end_df["dn"].iloc[-1] - recent_start_df["dn"].iloc[-1]
        # 有xp解析为0的情况，剔除异常情况
        recent_xp = (
            recent_end_df[recent_end_df["xp"] >= 0.0]["xp"].iloc[-1]
            - recent_start_df[recent_start_df["xp"] >= 0.0]["xp"].iloc[-1]
        )
        recent_gold = recent_end_df["gold"].iloc[-1] - recent_start_df["gold"].iloc[-1]
    elif not recent_end_df.empty:
        recent_lh = recent_end_df["lh"].iloc[-1]
        recent_dn = recent_end_df["dn"].iloc[-1]
        recent_xp = recent_end_df["xp"].iloc[-1]
        recent_gold = recent_end_df["gold"].iloc[-1]
    else:
        recent_lh = 0
        recent_dn = 0
        recent_xp = 0
        recent_gold = 0

    log_features = pd.DataFrame(
        {
            "early_lh": [early_lh],
            "early_dn": [early_dn],
            "early_xp": [early_xp],
            "early_gold": [early_gold],
            "recent_lh": [recent_lh],
            "recent_dn": [recent_dn],
            "recent_xp": [recent_xp],
            "recent_gold": [recent_gold],
        }
    )

    return log_features


def get_farm_feature(dfs, f_t, start_tick, end_tick, player_id_index=0):
    """组合当前时刻与时间窗口内的农经济特征，返回单个玩家的特征向量。"""
    tagert_columns = [
        "player_id",
        "tick",
        "lh",
        "dn",
        "xp",
        "kills",
        "deaths",
        "assists",
        "gold",
        "net_worth",
    ]
    players = dfs["players"]
    df_farmFeature = players[tagert_columns][players["player_id"] == player_id_index]

    df_ff_now0 = farm_feature_now(df_farmFeature, f_t, start_tick, end_tick)
    df_ff_log = farm_feature_log(df_farmFeature, f_t, start_tick, end_tick)

    combined = pd.concat(
        [df_ff_now0.reset_index(drop=True), df_ff_log.reset_index(drop=True)], axis=1
    )
    return combined
