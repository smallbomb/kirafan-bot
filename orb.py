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
        self.target = _orb_skill['target'].upper()
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

    def action(self) -> bool:
        if not self.use:
            return False

        self.__slide_out_orb_list()
        if self.__use_orb():
            logging.info('orb action: use orb0%s success' % self.option)
        else:
            logging.info('orb action: use orb0%s failed' % self.option)
        self.use = False
        return True

    def __use_orb(self) -> bool:
        if self.objects['option'].found():
            self.objects['option'].click(2)
            self.__click_target()
        if self.objects['cancel'].found():
            self.objects['cancel'].click(3)
            return False
        else:
            return True

    def __click_target(self):
        self.objects['option_submit'].click(1, 0.5)
        try:
            self.objects['target'].click(3)
        except KeyError:
            pass
        self.objects['target_cancel'].click(1, 1.5)

    def __slide_out_orb_list(self):
        destX = uData.setting['game_region'][0] + uData.setting['game_region'][2] - 1
        destY = self.objects['entrypoint'].coord[1]
        pyautogui.moveTo(*self.objects['entrypoint'].coord)
        pyautogui.dragTo(destX, destY, 1, button='left')


# Test
if __name__ == '__main__':
    orb = Orb('1')
    orb.action()
