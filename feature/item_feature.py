import pandas as pd


def get_item_dict(play_ext):
    """从重放解析器的 EntityNames 字符串表中提取所有物品名称，并构建索引映射。"""
    entity_names = play_ext._parser.string_tables.get_by_name("EntityNames")

    item_list = []
    for key in entity_names.items:
        if entity_names.items[key][0].startswith("item"):
            item_list.append(entity_names.items[key][0])

    item_loc_dict = {}
    for i in range(len(item_list)):
        item_loc_dict[item_list[i]] = i

    return item_loc_dict


def get_item_feature(
    inventory_tick,
    item_columns,
    f_t,
    start_tick,
    end_tick,
    item_loc_dict,
    player_id_index=0,
):
    """根据玩家当前时刻的物品栏，构建物品在集合中的二值特征向量。"""

    if f_t in inventory_tick and player_id_index in inventory_tick[f_t]:
        inventory = inventory_tick[f_t][player_id_index]
        item_feature = [0] * len(item_loc_dict)
        for slot, item in inventory.items():
            if item in item_loc_dict:
                item_feature[item_loc_dict[item]] = 1
        return pd.DataFrame([item_feature], columns=item_columns)

    return pd.DataFrame([[0] * len(item_loc_dict)], columns=item_columns)
