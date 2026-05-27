import numpy as np
import pandas as pd


def set_end_tick(row, end_tick):
    """为每个守卫记录计算结束 tick，优先使用 expires_tick，其次 killed_tick，否则使用赛局结束值。"""
    if np.isnan(row["expires_tick"]) == False:
        return row["expires_tick"]
    if np.isnan(row["killed_tick"]) == False:
        return row["killed_tick"]
    return end_tick


def get_ward_feature(wards, f_t, start_tick, end_tick):
    """统计指定时间段内各队的观察哨与岗哨数量特征。"""
    wards["end_tick"] = wards.apply(lambda row: set_end_tick(row, end_tick), axis=1)

    _w = wards[f_t <= wards["end_tick"]][f_t >= wards["tick"]]
    _w2 = wards[f_t >= wards["tick"]]
    _wk = wards[f_t >= wards["killed_tick"]]

    ward_features = pd.DataFrame(
        {
            "ward_s2": [_w[_w["team"] == 2][_w["ward_type"] == "sentry"]["player_id"].count()],
            "ward_s3": [_w[_w["team"] == 3][_w["ward_type"] == "sentry"]["player_id"].count()],
            "ward_o2": [_w[_w["team"] == 2][_w["ward_type"] == "observer"]["player_id"].count()],
            "ward_o3": [_w[_w["team"] == 3][_w["ward_type"] == "observer"]["player_id"].count()],
            "ward_hs2": [_w2[_w2["team"] == 2][_w2["ward_type"] == "sentry"]["player_id"].count()],
            "ward_hs3": [_w2[_w2["team"] == 3][_w2["ward_type"] == "sentry"]["player_id"].count()],
            "ward_ho2": [_w2[_w2["team"] == 2][_w2["ward_type"] == "observer"]["player_id"].count()],
            "ward_ho3": [_w2[_w2["team"] == 3][_w2["ward_type"] == "observer"]["player_id"].count()],
            "ward_kills2": [_wk[_wk["team"] == 2][_wk["ward_type"] == "sentry"]["player_id"].count()],
            "ward_kills3": [_wk[_wk["team"] == 3][_wk["ward_type"] == "sentry"]["player_id"].count()],
            "ward_killo2": [_wk[_wk["team"] == 2][_wk["ward_type"] == "observer"]["player_id"].count()],
            "ward_killo3": [_wk[_wk["team"] == 3][_wk["ward_type"] == "observer"]["player_id"].count()],
        }
    )

    return ward_features
