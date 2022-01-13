import json
import copy
from typeguard import typechecked
from defined import Dict


@typechecked
class _UserData():
    def __init__(self):
        with open('bot_setting.json', encoding="utf-8") as f:
            self.__raw = self.__padding(json.load(f))
        self.setting = self.__load()

    def __load(self) -> Dict:
        data = copy.deepcopy(self.__raw)
        self.__adb_region = tuple(data['game_region'][:2] + data['adb']['emulator_resolution'])
        self.__pyautogui_region = tuple(data['game_region'])
        data['ratio'] = data['ratio'][data['aspect_ratio']]
        data['game_region'] = self.__adb_region if data['adb']['use'] else self.__pyautogui_region
        data['quest_selector'] = data['questList']['quest_selector']
        quest = data['questList'][data['quest_selector']]
        data['loop_count'] = quest['loop_count']
        data['crea_stop'] = quest['crea_stop']
        data['stamina'] = quest['stamina']
        data['friend_support'] = quest['friend_support']
        data['orb'] = quest['orb']
        data['wave'] = quest['wave']
        del data['questList']
        return data

    def raw(self):
        return self.__raw

    def reload(self):
        old_region = self.setting['game_region']
        self.setting = self.__load()
        if self.region_is_init():
            self.setting['game_region'] = old_region

    def adb_mode_switch(self):
        self.setting['adb']['use'] = not self.setting['adb']['use']
        self.setting['game_region'] = self.__adb_region if self.setting['adb']['use'] else self.__pyautogui_region

    def region_is_init(self) -> bool:
        return all(x <= y for x, y in zip(self.setting['game_region'], (0, 0, 1, 1)))

    def __padding(self, rawdata: Dict) -> Dict:
        questlist = rawdata['questList']
        for q in tuple(filter(lambda x: x != 'quest_selector', questlist.keys())):
            self.__padding_friend_support(questlist[q])
            self.__padding_stamina(questlist[q])
            self.__padding_orb(questlist[q])
            self.__padding_wave(self.__wave_parse(questlist[q]['wave']))
        return rawdata

    def __padding_friend_support(self, quest: Dict):
        if 'friend_support' not in quest:
            quest['friend_support'] = {'use': False, 'wave_N': 1, 'myturn': 0, 'replace': 'character_left'}

    def __padding_stamina(self, quest: Dict):
        if 'stamina' not in quest:
            quest['stamina'] = {'use': False, 'priority': []}

    def __padding_orb(self, quest: Dict):
        if 'orb' not in quest:
            quest['orb'] = {'orb_name': ''}
        for opt in map(str, range(1, 4)):
            if opt not in quest['orb']:
                quest['orb'][opt] = {"use": False, "wave_N": 1, "myturn": 0, "target": "N"}

    def __padding_wave(self, wave: Dict):
        for N in map(str, range(1, wave['total'] + 1)):
            if 'sp_weight_enable' not in wave[N]:
                wave[N]['sp_weight_enable'] = False
            for p in ['left', 'middle', 'right']:
                if f'character_{p}' not in wave[N]:
                    wave[N][f'character_{p}'] = {'skill_priority': [], 'sp_weight': 1}
                elif 'sp_weight' not in wave[N][f'character_{p}']:
                    wave[N][f'character_{p}']['sp_weight'] = 1

    def __wave_parse(self, wave: Dict) -> Dict:
        for key in list(wave.keys()):
            if "," in key and key[0].isdigit():
                for sub_k in key.split(","):
                    if sub_k.isdigit():
                        wave[sub_k] = copy.deepcopy(wave[key])
                del wave[key]
        return wave

    def save(self):
        with open('bot_setting.json', 'w', encoding="utf-8") as f:
            json.dump(self.__raw, f, ensure_ascii=False)


uData = _UserData()
