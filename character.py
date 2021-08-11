import logging
from defined import List
from data import uData
from object import Load_Objects


class Character:
    def __init__(self, character_id: int, wave_id: int):
        _character = uData.setting['wave'][str(wave_id)]['character_{}'.format(character_id)]
        self.id = character_id
        self.wave_id = wave_id
        self.objects = Load_Objects("character")
        self.sk_priority = _character['skill_priority'] + ['auto_button']
        self.sp_weight = _character['sp_weight'] if 'sp_weight' in _character else 1
        self.sp_use = 'sp' in self.sk_priority
        self.sp_sleep = uData.setting['sleep']['sp']

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)

    def current(self):
        return self.objects['focus_ch{}'.format(self.id)].found()

    def action(self, chars_sp_order: List) -> str:
        '''@return skillname which skill be used?
        '''
        ck_animate_cd = True
        sp_id = chars_sp_order[0] if chars_sp_order else self.id

        for sk in self.sk_priority:
            logging.debug('character action: %s is checked now' % sk)
            if self.__skill_is_ready(sk):
                if sk == 'auto_button':
                    self.__action_auto_button()
                elif sk == 'sp':
                    if self.id == sp_id:
                        self.__action_sp()
                    elif self.objects['sp_charge2'].found():
                        self.__action_sp()
                        sk += '2'
                    else:
                        continue
                else:
                    self.objects[sk].click(4)
                    if sk == 'weapon_sk' and self.current():
                        continue  # has no weapons
                logging.debug('character action: %s finsih' % sk)
                return sk
            elif ck_animate_cd and sk in ['sk1', 'sk2', 'weapon_sk']:
                ck_animate_cd = False
                if self.__action_cd_skill(sk):
                    logging.debug('character action: %s finsih' % sk)
                    return sk

    def __skill_is_ready(self, sk: str) -> bool:
        if sk in ['normal_atk', 'auto_button']:
            return True
        return self.objects[sk].found()

    def __action_cd_skill(self, sk: str) -> bool:
        # success: True, Failed: False
        if not self.objects['{}_cd'.format(sk)].found():
            return False
        logging.debug('character action: try to click {} 0.5 sec (skill cd now?)'.format(sk))
        self.objects[sk].click_sec(0.6, 0.13)
        if self.current():
            return False
        return True

    def __action_auto_button(self):
        while not self.objects['auto_button'].found():
            self.objects['auto_button'].click()
        self.objects['center'].click(2)

    def __action_sp(self):
        self.objects['sp'].click(2)
        while not self.objects['sp_cancel'].found():
            self.objects['sp'].click(2)
        while not self.objects['sp_ch1_set'].found():
            self.objects['sp_ch1'].click()
        self.objects['sp_submit'].click(3)
        self.objects['center'].click_sec(self.sp_sleep, 0.5)
