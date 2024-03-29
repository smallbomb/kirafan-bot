from log import logger
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

        while not self.__slide_out_orb_list():
            logger.debug('orb action(): slide out orb list failed... try again')

        if self.__use_orb():
            logger.debug(f'orb action(): use orb0{self.option} success')
        else:
            logger.debug(f'orb action(): use orb0{self.option} failed')
        self.use = False
        return True

    def __use_orb(self) -> bool:
        if self.objects['option'].found(False):
            self.objects['option'].click(2)
            self.__click_target()
        if self.objects['cancel'].found():
            self.objects['cancel'].click(2)
            return False
        else:
            return True

    def __click_target(self):
        self.objects['option_submit'].click(1, 0.5)
        try:
            self.objects['target'].click(3)
        except KeyError:  # target is 'N'
            pass
        self.objects['target_cancel'].click(1, 1)

    def __slide_out_orb_list(self) -> bool:
        destX = uData.setting['game_region'][0] + uData.setting['game_region'][2] - 1
        destY = self.objects['entrypoint'].coord[1]
        self.objects['entrypoint'].swipe(destX, destY, 1)
        return self.objects['cancel'].found()

    def adb_mode_switch(self):
        self.objects = self.__object_init()


# Test
if __name__ == '__main__':
    orb = Orb('1')
    orb.action()
