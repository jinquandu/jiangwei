import os
from gem.parser import ReplayParser
from gem.extractors.players import PlayerExtractor
import gem
import pickle
import requests
import bz2
import shutil
import time
from pathlib import Path

from config import DECOMPRESS_DIR, MATCH_DIR, REPLAY_DIR, ensure_runtime_dirs


def download_replay(file_name,replay_url,match_id):
    max_retries=3
    retry_delay=2
    for attempt in range(1, max_retries + 1):
        try:
            # stream=True 非常重要，用于大文件下载
            with requests.get(replay_url, stream=True, timeout=30) as r:
                r.raise_for_status()
                
                # 获取文件总大小 (MB)
                total_size = int(r.headers.get('content-length', 0)) / (1024 * 1024)
                print(f"📥 文件大小约为: {total_size:.2f} MB")
                
                # 确保目录存在
                os.makedirs(os.path.dirname(file_name), exist_ok=True)
                
                with open(file_name, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:  # 过滤掉 keep-alive 的新 chunk
                            f.write(chunk)

            print(f"🎉 下载完成！文件已保存为: {file_name}")
            return  # 成功后直接退出函数

        except Exception as e:
            print(f"❌ 第 {attempt} 次下载出错: {e}, 文件: {file_name}")
            if attempt < max_retries:
                print(f"⏳ {retry_delay} 秒后重试...")
                time.sleep(retry_delay)
            else:
                print("⚠️ 已达到最大重试次数，放弃下载。")

class InventoryPlayerExtractor(PlayerExtractor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.inventory_by_tick: dict[int, dict[int, dict[int, str]]] = {}  # tick -> player_id -> slot -> item
        self.herostatus_by_tick: dict[int, dict[int, dict[int, str]]] = {} # tick -> player_id -> tyoe -> value

    def _sample(self, tick, minute=False):
        super()._sample(tick, minute)
        self.inventory_by_tick[tick] = {}
        self.herostatus_by_tick[tick] = {}
        for snap in self.snapshots:
            if snap.tick == tick:
                # 找到对应 hero entity
                hero_entity = self._heroes_by_npc.get(snap.npc_name)
                if hero_entity:
                    inv = self._read_inventory(hero_entity)
                    self.inventory_by_tick[tick][snap.player_id] = inv

                    status_dict = {}
                    status_dict["level"] = snap.level
                    status_dict["hp"] =  snap.hp
                    status_dict["max_hp"] = snap.max_hp
                    status_dict["mp"] = snap.mana
                    status_dict["max_mp"] = snap.max_mana

                    self.herostatus_by_tick[tick][snap.player_id] = status_dict



def decompress_bz2(bz2_file_path, output_file_path):
    with bz2.BZ2File(bz2_file_path, 'rb') as f_in:
        with open(output_file_path, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
            

def replay2data(replay_path,data_path,match_id):
    # print(f"🎉 解析录像...{replay_path}")
    # 数据准备 

    start_time = time.time()
    match = gem.parse(replay_path)
    dfs = gem.parse_to_dataframe(replay_path)
    parser = ReplayParser(replay_path)
    play_ext = InventoryPlayerExtractor(sample_interval=30)  # 每30 tick采样，减少内存
    play_ext.attach(parser)
    parser.parse()
    
    # 数据打包
    match_data = {}
    match_data["match"] = match
    match_data["dfs"] = dfs
    match_data["inventory"] = play_ext.inventory_by_tick
    match_data["hero_status"] = play_ext.herostatus_by_tick

    # 保存到文件
    with open(data_path, 'wb') as f:
        pickle.dump(match_data, f)

    end_time = time.time()
    print(f"🎉 转化完成...总耗时: {match_id}:{end_time - start_time:.2f} 秒")

def onereplay2data(replay_path,replay_url,match_id):
    ensure_runtime_dirs()
    replay_dir = Path(replay_path)
    file_name = replay_url.split("/")[-1]
    replay_file_path = replay_dir / file_name
    decompress_file_name = DECOMPRESS_DIR / file_name.replace(".bz2", "")
    data_path = MATCH_DIR / f"{decompress_file_name.stem}.mad"

    # replay下载
    download_replay(str(replay_file_path), replay_url, match_id)
    # replay文件解压
    decompress_bz2(str(replay_file_path), str(decompress_file_name))
    # 文件转化数据
    replay2data(str(decompress_file_name), str(data_path), match_id)
