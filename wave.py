from defined import List, Coord, Optional
from typeguard import typechecked
from data import uData
from icon import Icon
from object import Load_Objects
from character import Character


@typechecked
def gen_circle_list(start: int, length: int) -> List:
    lst = list(range(1, length + 1))
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
        self.ch_id = 3
        self.total = total
        self.auto = _wave[str(self.id)]['auto']
        self.name = 'wave_{0}-{1}'.format(self.id, self.total)
        self.objects = Load_Objects("wave")
        self.characters = {str(i): Character(i, self.id) for i in range(1, 4)}
        self.chars_sp_order = self.__sp_order_init() if _wave[str(self.id)]['sp_weight_enable'] else []
        self.icon = Icon('{}.png'.format(self.name), _wave['confidence'], _wave['grayscale'])

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)

    def current(self) -> bool:
        return True if self.icon.found() else False

    def __sp_order_init(self) -> List:
        order = list()
        for i in range(1, 4):
            order = riffle(order, [i] * int(self.characters[str(i)].sp_use) * self.characters[str(i)].sp_weight)
        return order

    def update_characterID(self) -> bool:
        for c in gen_circle_list(self.ch_id % 3 + 1, 3):
            if self.characters[str(c)].current():
                self.ch_id = c
                return True
        return False

    def charater_action(self):
        sk = self.characters[str(self.ch_id)].action(self.chars_sp_order)
        if sk == 'sp' and self.chars_sp_order:
            self.chars_sp_order.append(self.chars_sp_order.pop(0))

    def is_myTurn(self) -> bool:
        return self.objects['setting_button'].found()

    def get_icon_coord(self) -> Optional[Coord]:
        return self.icon.get_center()


# Test
if __name__ == '__main__':
    wave = Wave(1, 5)
    print(wave.chars_sp_order)
