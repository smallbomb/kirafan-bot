import logging
from defined import List
from data import uData
from object import Load_Objects


class Character:
    def __init__(self, character_id: int, wave_id: int):
        self.id = character_id
        self.wave_id = wave_id
        self.objects = Load_Objects("character")
        _character = uData.setting['wave'][str(self.wave_id)]['character_{}'.format(self.id)]
        self.sk_priority = _character['skill_priority'] + ['auto_button']
        self.sp_weight = _character['sp_weight']
        self.sp_use = 'sp' in self.sk_priority
        self.sp_sleep = uData.setting['sleep']['sp']

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)

    def current(self):
        return self.objects['focus_ch{}'.format(self.id)].found()

    def sp_priority(self):
        return self.sk_priority.index("sp")

    def action(self, chars_sp_order: List) -> str:
        animate_cd = True
        sp_id = chars_sp_order[0] if chars_sp_order else self.id

        for sk in self.sk_priority:
            logging.debug('character action: %s is checked now' % sk)
            sk_found = True if sk == 'normal_atk' else self.objects[sk].found() if sk != 'auto_button' else not self.objects[sk].found()
            if sk_found:
                logging.debug('character action: %s' % sk)
                if sk == 'auto_button':
                    while not self.objects[sk].found(): self.objects[sk].click()
                    self.objects['center'].click(2)
                elif sk == 'sp':
                    if self.id == sp_id or self.objects['sp_charge2'].found():
                        self.objects[sk].click(2)
                        while not self.objects['sp_cancel'].found(): continue
                        while not self.objects['sp_ch1_set'].found(): self.objects['sp_ch1'].click(1)
                        self.objects['sp_submit'].click(3)
                        self.objects['center'].click_sec(self.sp_sleep, 0.5)
                        if self.id != sp_id: return 'sp2' # sp_charge2 found
                    else:
                        continue
                else:
                    self.objects[sk].click(4)
                return sk
            elif animate_cd and sk in ['sk1', 'sk2', 'weapon_sk']:
                animate_cd = False 
                if self.objects['{}_cd'.format(sk)].found():
                    logging.debug('character action: wait skill cd animation 0.5 sec')
                    self.objects[sk].click_sec(0.6, 0.13)
                    if not self.current():
                        logging.debug('character action: %s' % sk)
                        return sk
