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
        self.use = _orb_skill['use']
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
            elif key.startswith('orb_') and (key.endswith('cancel') or key.endswith('entrypoint') or key.endswith('submit')):
                ret[key[4:]] = value
        return ret

    def action(self):
        if not self.use:
            return
        logging.critical('orb test: show orb list')
        self.__show_orb_list()
        logging.critical('orb test: use_orb')
        if self.__use_orb():
            logging.critical('use orb0(%s) skill success' % self.option)
        else:
            logging.critical('use orb0(%s) skill failed' % self.option)

    def __use_orb(self) -> bool:
        if self.objects['option'].found():
            logging.critical('orb test: option found')
            self.objects['option'].click(1, 0.5)
            self.__click_target()
        if self.objects['cancel'].found():
            logging.critical('orb test: option cancel found')
            self.objects['cancel'].click(1, 0.5)
            return False
        else:
            return True

    def __click_target(self):
        self.objects['option_submit'].click(1, 0.5)
        try:
            self.objects['target'].click()
        except KeyError:
            pass
        self.objects['target_cancel'].click(1, 0.5)

    def __show_orb_list(self):
        destX = uData.setting['game_region'][0] + uData.setting['game_region'][2] - 1
        destY = self.objects['entrypoint'].coord[1]
        pyautogui.moveTo(*self.objects['entrypoint'].coord)
        pyautogui.dragTo(destX, destY, 0.3, button='left')


# Test
if __name__ == '__main__':
    orb = Orb('1')
    print(orb.action())
