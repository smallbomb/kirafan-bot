import json
from typeguard import typechecked
from defined import Dict


@typechecked
class _UserData():
    def __init__(self):
        self.setting = self.__load()

    def __load(self) -> Dict:
        with open('setting.json') as f:
            data = json.load(f)
        data['ratio'] = data['ratio'][data['aspect_ratio']]
        data['game_region'] = tuple(data['game_region'])
        return data

    def reload(self):
        old_region = self.setting['game_region']
        self.setting = self.__load()
        if self.region_is_init():
            self.setting['game_region'] = old_region

    def region_is_init(self) -> bool:
        return all(x <= y for x, y in zip(self.setting['game_region'], (0, 0, 1, 1)))


uData = _UserData()
