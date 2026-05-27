import pandas as pd


def get_position_feature(positions, f_t, start_tick, end_tick, player_id_index=0):
    """基于玩家的位置信息，统计上路、中路、下路、野区的停留时间，并返回当前位置信息特征。"""
    player_positions = positions[
        (positions["player_id"] == player_id_index)
        & (positions["tick"] >= start_tick)
        & (positions["tick"] <= f_t)
    ].copy()

    if player_positions.empty:
        return pd.DataFrame(
            [
                {
                    "top_time_s": 0.0,
                    "mid_time_s": 0.0,
                    "bottom_time_s": 0.0,
                    "jungle_time_s": 0.0,
                    "other_time_s": 0.0,
                    "top_time_ratio": 0.0,
                    "mid_time_ratio": 0.0,
                    "bottom_time_ratio": 0.0,
                    "jungle_time_ratio": 0.0,
                    "other_time_ratio": 0.0,
                    "current_x": None,
                    "current_y": None,
                    "current_zone": "unknown",
                    "current_is_top": 0,
                    "current_is_mid": 0,
                    "current_is_bottom": 0,
                    "current_is_jungle": 0,
                    "current_is_other": 0,
                }
            ]
        )

    player_positions = player_positions.sort_values("tick").reset_index(drop=True)

    def classify_zone(wx: float, wy: float, team: int) -> str:
        _MID_BAND = 2000
        _MID_X_MIN = 10500
        _MID_X_MAX = 22000
        _SAFE_R_Y_MAX = 12500
        _SAFE_R_X_MIN = 20000
        _SAFE_R_Y_MID = 16000
        _OFF_R_X_MAX = 12500
        _OFF_R_Y_MIN = 19000

        if abs(wx - wy) < _MID_BAND and _MID_X_MIN < wx < _MID_X_MAX:
            return "mid"

        is_safe_r = (wy < _SAFE_R_Y_MAX) or (wx > _SAFE_R_X_MIN and wy < _SAFE_R_Y_MID)
        is_off_r = (wx < _OFF_R_X_MAX) and (wy > _OFF_R_Y_MIN)

        if is_safe_r:
            return "bottom" if team == 2 else "top"
        if is_off_r:
            return "top" if team == 2 else "bottom"
        if _OFF_R_X_MAX <= wx <= _SAFE_R_X_MIN and _SAFE_R_Y_MAX <= wy <= _OFF_R_Y_MIN:
            return "jungle"
        return "other"

    team = int(player_positions["team"].iloc[0])
    player_positions["duration"] = (
        player_positions["tick"].shift(-1).fillna(f_t) - player_positions["tick"]
    )
    if len(player_positions) > 0:
        last_index = player_positions.index[-1]
        last_tick = player_positions.at[last_index, "tick"]
        player_positions.at[last_index, "duration"] = max(0, f_t - last_tick)

    player_positions["zone"] = player_positions.apply(
        lambda row: classify_zone(row["x"], row["y"], team), axis=1
    )
    player_positions["time_s"] = player_positions["duration"] / 30.0

    zone_time = player_positions.groupby("zone")["time_s"].sum().to_dict()
    total_time = sum(zone_time.values())
    top_time = float(zone_time.get("top", 0.0))
    mid_time = float(zone_time.get("mid", 0.0))
    bottom_time = float(zone_time.get("bottom", 0.0))
    jungle_time = float(zone_time.get("jungle", 0.0))
    other_time = float(zone_time.get("other", 0.0))

    top_time_ratio = top_time / total_time if total_time > 0 else 0.0
    mid_time_ratio = mid_time / total_time if total_time > 0 else 0.0
    bottom_time_ratio = bottom_time / total_time if total_time > 0 else 0.0
    jungle_time_ratio = jungle_time / total_time if total_time > 0 else 0.0
    other_time_ratio = other_time / total_time if total_time > 0 else 0.0

    current_row = player_positions[player_positions["tick"] <= f_t].iloc[-1]
    current_zone = classify_zone(current_row["x"], current_row["y"], team)
    current_x = float(current_row["x"])
    current_y = float(current_row["y"])

    return pd.DataFrame(
        [
            {
                "top_time_s": top_time,
                "mid_time_s": mid_time,
                "bottom_time_s": bottom_time,
                "jungle_time_s": jungle_time,
                "other_time_s": other_time,
                "top_time_ratio": top_time_ratio,
                "mid_time_ratio": mid_time_ratio,
                "bottom_time_ratio": bottom_time_ratio,
                "jungle_time_ratio": jungle_time_ratio,
                "other_time_ratio": other_time_ratio,
                "current_x": current_x,
                "current_y": current_y,
                "current_zone": current_zone,
                "current_is_top": int(current_zone == "top"),
                "current_is_mid": int(current_zone == "mid"),
                "current_is_bottom": int(current_zone == "bottom"),
                "current_is_jungle": int(current_zone == "jungle"),
                "current_is_other": int(current_zone == "other"),
            }
        ]
    )
