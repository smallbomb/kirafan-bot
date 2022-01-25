from defined import List, Coord, Optional, CharaID
from typeguard import typechecked
from data import uData
from icon import Icon
from object import Load_Objects
from character import Character
from orb import Orb


@typechecked
def gen_circle_list(start: int, length: int, df_list: Optional[List] = None) -> List:
    lst = df_list or list(range(1, length + 1))
    return lst[start - 1:] + lst[0:start - 1]


@typechecked
def riffle(list1: List, list2: List) -> List:
    num1, num2 = len(list1), len(list2)
    if num1 < num2:
        list1, num1, list2, num2 = list2, num2, list1, num1

    if num2 == 0:
        return list1
    elif num2 == 1:
        average = num1 // (num2 + 1)
        return list1[:average] + list2 + list1[average:]
    else:
        average = round(num1 / num2)
        ret = []
        for i in range(0, num2):
            ret += list1[average * i:average * (i + 1)] + [list2[i]]
        return ret + list1[num2 * average:]


@typechecked
class Wave:
    def __init__(self, id_: int, total: int):
        _wave = uData.setting['wave']
        self.id = id_
        self.ch_id = 'right'
        self.__chara_list = ['left', 'middle', 'right']
        self.total = total
        self.__myTurn_count = 0
        self.auto = _wave[str(self.id)]['auto']
        self.name = f'wave_{self.id}-{self.total}'
        self.objects = Load_Objects("wave")
        self.icon = Icon(f'{self.name}.png', uData.setting['confidence'])
        if not self.auto:
            self.characters = {c: Character(c, self.id) for c in self.__chara_list}
            self.chars_sp_order = self.__sp_order_init() if 'sp_weight_enable' in _wave[str(self.id)] and _wave[str(self.id)]['sp_weight_enable'] else []  # noqa: E501
            self.orbs = self.__orb_init()
            self.__friend = uData.setting['friend_support'] if uData.setting['friend_support'] and uData.setting['friend_support']['wave_N'] == self.id else None  # noqa: E501
        self.__auto_button_multi_check = 0

    def __str__(self):
        string = str(self.__class__) + ":\n"
        for item in self.__dict__:
            if item in ['objects', 'characters', 'icon', 'orbs']:
                if type(self.__dict__[item]) == dict:
                    for value in self.__dict__[item].values():
                        string += item + str(value) + "\n\n"
                elif type(self.__dict__[item]) == list:
                    for value in self.__dict__[item]:
                        string += item + str(value) + "\n\n"
            else:
                string += "{item} = {self.__dict__[item]}\n\n"
        return string

    def __sp_order_init(self) -> List[CharaID]:
        order = list()
        for c in self.__chara_list:
            order = riffle(order, [c] * int(self.characters[c].sp_use) * self.characters[c].sp_weight)
        return order

    def __orb_init(self) -> List:
        if not uData.setting['orb']:
            return []

        lst = list()
        for i in range(1, 4):
            if str(i) in uData.setting['orb'] and self.id == uData.setting['orb'][str(i)]['wave_N']:
                lst.append(Orb(str(i)))
        return lst

    def current(self, adb_update_cache: bool) -> bool:
        return True if self.icon.found(adb_update_cache) else False

    def character_found(self) -> bool:
        for c in gen_circle_list(self.__chara_list.index(self.ch_id) + 1, len(self.__chara_list), self.__chara_list):
            if self.characters[c].ready(False):
                self.ch_id = c  # update current character ID
                return True
        return False

    def orb_action(self) -> bool:
        for orb in self.orbs:
            if orb.turn == self.__myTurn_count and orb.action():
                return True
        return False

    def friend_action(self) -> bool:
        if self.__friend is None or ('use' in self.__friend and not self.__friend['use']) or self.__myTurn_count != self.__friend['myturn']:  # noqa: E501
            return False
        elif not self.objects['friend'].found(False):
            return False

        self.objects['friend'].click(3, 0.3)
        if self.objects['friend_ok'].found(True):  # found it because player's character maybe less than 3.
            target = self.__friend['replace'].lower().replace('character', 'friend_replace')
            self.objects[target].click(3)
        self.objects['friend_ok'].click(2, 2.3)  # for sleep 2*2.3 = 4.6s
        return True

    def charater_action(self):
        sk = self.characters[self.ch_id].action(self.chars_sp_order)
        if sk == 'sp' and self.chars_sp_order:
            self.chars_sp_order.append(self.chars_sp_order.pop(0))
        self.__myTurn_count += 1

    def auto_click(self):
        if self.objects['auto_button'].found(False):  # auto_button is blue
            self.__auto_button_multi_check = 0
        else:
            self.__auto_button_multi_check += 1

        if self.__auto_button_multi_check > 2:
            self.objects['auto_button'].click()
            self.__auto_button_multi_check = 0

    def is_myTurn(self) -> bool:
        if self.auto:
            return self.objects['setting_button'].found(False)
        return (self.objects['setting_button'].found(False) and
                self.characters[self.ch_id].objects['atk'].found(False))

    def icon_coord(self, adb_update_cache: bool) -> Optional[Coord]:
        return self.icon.get_center(adb_update_cache)

    def reset(self):
        _wave = uData.setting['wave']
        self.ch_id = 'right'
        self.__myTurn_count = 0
        if not self.auto:
            self.chars_sp_order = self.__sp_order_init() if 'sp_weight_enable' in _wave[str(self.id)] and _wave[str(self.id)]['sp_weight_enable'] else []  # noqa: E501
            self.orbs = self.__orb_init()
        self.__auto_button_multi_check = 0

    def adb_mode_switch(self):
        self.objects = Load_Objects("wave")
        self.icon = Icon(f'{self.name}.png', uData.setting['confidence'])
        if not self.auto:
            for c in self.__chara_list:
                self.characters[c].adb_mode_switch()
            for orb in self.orbs:
                orb.adb_mode_switch()


# Test
if __name__ == '__main__':
    wave = Wave(3, 3)
    print(wave.chars_sp_order)
    print(len(wave.orbs))
    print(wave.orbs)
    wave.friend_action()
