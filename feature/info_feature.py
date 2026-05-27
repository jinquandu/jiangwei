import pandas as pd


def get_info_feature(dfs, f_t, start_tick, end_tick):
    """构建当前时刻的全局比赛信息特征。"""
    objectives = dfs.get("objectives", pd.DataFrame())
    positions = dfs.get("positions", pd.DataFrame())

    game_tick = max(0, f_t - start_tick)
    game_seconds = game_tick / 30.0
    game_minutes = game_seconds / 60.0
    game_progress = game_tick / max(1, end_tick - start_tick)

    roshan_alive = 1
    roshan_respawn_window = 0
    roshan_kills = 0
    roshan_seconds_since_kill = -1.0
    roshan_seconds_until_min_respawn = 0.0
    roshan_seconds_until_max_respawn = 0.0

    if not objectives.empty and "type" in objectives.columns:
        roshan_rows = objectives[
            (objectives["type"] == "roshan") & (objectives["tick"] <= f_t)
        ].sort_values("tick")
        roshan_kills = int(len(roshan_rows))

        if not roshan_rows.empty:
            last_roshan_tick = int(roshan_rows.iloc[-1]["tick"])
            ticks_since_last_roshan = max(0, f_t - last_roshan_tick)
            roshan_seconds_since_kill = ticks_since_last_roshan / 30.0

            min_respawn_ticks = 8 * 60 * 30
            max_respawn_ticks = 11 * 60 * 30

            if ticks_since_last_roshan < min_respawn_ticks:
                roshan_alive = 0
                roshan_respawn_window = 0
                roshan_seconds_until_min_respawn = (
                    min_respawn_ticks - ticks_since_last_roshan
                ) / 30.0
                roshan_seconds_until_max_respawn = (
                    max_respawn_ticks - ticks_since_last_roshan
                ) / 30.0
            elif ticks_since_last_roshan < max_respawn_ticks:
                roshan_alive = 0
                roshan_respawn_window = 1
                roshan_seconds_until_min_respawn = 0.0
                roshan_seconds_until_max_respawn = (
                    max_respawn_ticks - ticks_since_last_roshan
                ) / 30.0
            else:
                roshan_alive = 1
                roshan_respawn_window = 0

    return pd.DataFrame(
        [
            {
                "game_time_seconds": game_seconds,
                "roshan_alive": roshan_alive,
            }
        ]
    )
