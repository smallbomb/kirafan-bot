import json
from typeguard import typechecked
from defined import Dict


@typechecked
def _wave_parse(wave: Dict) -> Dict:
    for key in list(wave.keys()):
        if "," in key and key[0].isdigit():
            for sub_k in key.split(","):
                if sub_k.isdigit():
                    wave[sub_k] = wave[key]
            del wave[key]
    return wave


@typechecked
class _UserData():
    def __init__(self):
        self.setting = self.__load()

    def __load(self) -> Dict:
        with open('setting.json', encoding="utf-8") as f:
            data = json.load(f)
        data['ratio'] = data['ratio'][data['aspect_ratio']]
        data['game_region'] = tuple(data['game_region'])
        data['quest_selector'] = data['questList']['quest_selector']
        quest = data['questList'][data['quest_selector']]
        data['loop_count'] = quest['loop_count']
        data['crea_stop'] = quest['crea_stop']
        data['stamina'] = quest['stamina'] if "stamina" in quest else None
        data['friend_support'] = quest['friend_support'] if "friend_support" in quest else None
        data['orb'] = quest['orb'] if "orb" in quest else None
        data['wave'] = _wave_parse(quest['wave'])
        del data['questList']
        return data

    def reload(self):
        old_region = self.setting['game_region']
        self.setting = self.__load()
        if self.region_is_init():
            self.setting['game_region'] = old_region

    def region_is_init(self) -> bool:
        return all(x <= y for x, y in zip(self.setting['game_region'], (0, 0, 1, 1)))


uData = _UserData()
