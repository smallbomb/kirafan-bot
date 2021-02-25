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
        self.usable = _orb_skill['use']
        self.turn = _orb_skill['myturn']
        self.target = str(_orb_skill['target'])
        self.objects = self.__object_init(opt_num)

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)

    def __object_init(self, opt_num: str) -> Dict:
        ret = dict()
        for (key, value) in Load_Objects('orb').items():
            if key == 'orb':
                ret['call'] = value
            elif key.startswith('orb_option') and key[-1] == opt_num:
                ret['option'] = value
            elif key.startswith('orb_target') and key[-1] == self.target:
                ret['target'] = value
            elif key.startswith('orb_') and key.rfind('cancel') >= 0:
                ret[key[4:]] = value
        return ret

    def action(self) -> bool:
        if not self.usable:
            return False
        logging.critical('orb test: start')
        self.usable = False
        logging.critical('orb test: show orb list')
        self.__show_orb_list()
        logging.critical('orb test: show use_orb')
        return self.__use_orb()

    def __use_orb(self) -> bool:
        if self.objects['option'].found():
            self.objects['option'].click()
            logging.critical('orb test: option found')
        try:
            if self.objects['target'].found():
                logging.critical('orb test: target found')
                self.objects['target'].click()
                return True
            logging.critical('orb test: target cancel click')
            self.objects['target_cancel'].click()
        except KeyError:
            return True
        logging.critical('orb test: option cancel click')
        self.objects['option_cancel'].click()
        return False

    def __show_orb_list(self):
        destX = uData.setting['game_region'][0] + uData.setting['game_region'][2] - 1
        destY = self.objects['call'].coord[1]
        pyautogui.moveTo(*self.objects['call'].coord)
        pyautogui.dragTo(destX, destY, 0.5, button='left')


# Test
if __name__ == '__main__':
    orb = Orb('1')
    print(orb.action())
