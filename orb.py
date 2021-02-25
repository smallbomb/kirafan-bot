import logging
import pyautogui
from defined import Dict
from data import uData
from typeguard import typechecked
from object import Load_Objects


@typechecked
class Orb:
    def __init__(self, opt_num: str):
        _orb_skill = uData.setting['orb'][opt_num]
        self.option = opt_num
        self.usable = _orb_skill['use']
        self.turn = _orb_skill['myturn']
        self.target = str(_orb_skill['target'])
        self.objects = self.__object_init()

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)

    def __object_init(self) -> Dict:
        ret = dict()
        for (key, value) in Load_Objects('orb').items():
            if key.startswith('orb_option') and key[-1] == self.option:
                ret['option'] = value
            elif key.startswith('orb_target') and key[-1] == self.target:
                ret['target'] = value
            elif key.startswith('orb_') and (key.rfind('cancel') >= 0 or key.rfind('entrypoint') >= 0 or key.rfind('sumbit')):
                ret[key[4:]] = value
        return ret

    def action(self) -> bool:
        if not self.usable:
            return False
        logging.critical('orb test: start')
        self.usable = False
        logging.critical('orb test: show orb list')
        self.__show_orb_list()
        logging.critical('orb test: use_orb')
        return self.__use_orb()

    def __use_orb(self) -> bool:
        if self.objects['option'].found():
            self.objects['option'].click(1, 0.5)
            logging.critical('orb test: option found')
            self.__click_target()  # True or False
        logging.critical('orb test: option cancel click')
        self.objects['cancel'].click()
        return False

    def __click_target(self):
        logging.critical('orb test: error target key element')
        self.objects['option_submit'].click(1, 0.5)
        try:
            self.objects['target'].click()
        except KeyError:
            pass
        logging.critical('orb test: target cancel click')
        self.objects['target_cancel'].click(1, 0.5)

    def __show_orb_list(self):
        destX = uData.setting['game_region'][0] + uData.setting['game_region'][2] - 1
        destY = self.objects['entrypoint'].coord[1]
        pyautogui.moveTo(*self.objects['entrypoint'].coord)
        pyautogui.dragTo(destX, destY, 1.3, button='left')


# Test
if __name__ == '__main__':
    orb = Orb('1')
    # print(orb.objects['option'])
    print(orb.action())
