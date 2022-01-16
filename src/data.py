import copy
import commentjson as json
from typeguard import typechecked
from defined import Dict

__VERSION__ = '3.0.0'


@typechecked
class _UserData():
    def __init__(self):
        self.__basic_setting = self.__adv_setting = None
        self.setting = self.__load()

    def __load_file(self, fname: str) -> Dict:
        with open(fname, encoding="utf-8") as f:
            d = json.load(f)
        return d

    def __load(self) -> Dict:
        self.__adv_setting = self.__load_file('advanced_setting.jsonc')
        if self.__basic_setting is None or self.__adv_setting['mode'] == 'hotkey':
            self.__basic_setting = self.__padding(self.__load_file('bot_setting.json'))

        data = copy.deepcopy(self.__basic_setting)
        for k in list(filter(lambda s: s != 'ratio', self.__adv_setting.keys())):
            data[k] = self.__adv_setting[k]
        data['ratio'] = self.__adv_setting['ratio'][self.__adv_setting['aspect_ratio']]
        self.__adb_region = tuple(data['game_region'][:2] + data['adb']['emulator_resolution'])
        self.__pyautogui_region = tuple(data['game_region'])
        data['game_region'] = self.__adb_region if data['adb']['use'] else self.__pyautogui_region
        data['quest_selector'] = data['questList']['quest_selector']
        quest = data['questList'][data['quest_selector']]
        data['loop_count'] = quest['loop_count']
        data['crea_stop'] = quest['crea_stop']
        data['stamina'] = quest['stamina']
        data['friend_support'] = quest['friend_support']
        data['orb'] = quest['orb']
        data['wave'] = quest['wave']
        data['version'] = __VERSION__
        del data['questList']
        return data

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
        if len(questlist) == 1:
            questlist['default'] = {'loop_count': 5, 'crea_stop': False, 'wave': {'total': 1, '1': {"auto": True}}}
            questlist['quest_selector'] = 'default'
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

    def gui_setting(self):
        return self.__basic_setting

    def save_gui_setting(self):
        with open('bot_setting.json', 'w', encoding="utf-8") as f:
            json.dump(self.__basic_setting, f, ensure_ascii=False)


uData = _UserData()
