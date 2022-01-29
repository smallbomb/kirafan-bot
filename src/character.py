from log import logger
from defined import List, CharaID
from data import uData
from object import Load_Objects


class Character:
    def __init__(self, character_id: CharaID, wave_id: int):
        _character = uData.setting['wave'][str(wave_id)][f'character_{character_id}']
        self.id = character_id
        self.wave_id = wave_id
        self.objects = Load_Objects("character")
        self.sk_priority = _character['skill_priority'] + ['auto_button']
        self.sp_weight = _character['sp_weight'] if 'sp_weight' in _character else 1
        self.sp_use = 'sp' in self.sk_priority
        self.sp_sleep = uData.setting['sleep']['sp']

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)

    def ready(self, adb_update_cache: bool):
        return self.objects[f'focus_ch_{self.id}'].found(adb_update_cache)

    def action(self, chars_sp_order: List[CharaID]) -> str:
        '''@return skillname which skill be used?
        '''
        ck_animate_cd = True
        sp_id = chars_sp_order[0] if chars_sp_order else self.id

        for sk in self.sk_priority:
            logger.debug(f'character action: {sk:<11} is checked now')
            if self.__skill_is_ready(sk):
                if sk == 'auto_button':
                    self.__action_auto_button()
                elif sk == 'sp':
                    if self.id == sp_id:
                        self.__action_sp()
                    elif self.objects['sp_charge2'].found(False):
                        self.__action_sp()
                        sk += '2'
                    else:
                        continue
                else:
                    self.objects[sk].click(4)
                    if sk == 'wpn_sk' and self.ready(True):
                        continue  # has no weapons
                logger.debug(f'character action: use \x1b[32m{sk}\x1b[0m')
                return sk
            elif ck_animate_cd and sk in ['wpn_sk', 'L_sk', 'R_sk']:
                ck_animate_cd = False
                if self.__action_cd_skill(sk):
                    logger.debug(f'character action: use \x1b[32m{sk}\x1b[0m')
                    return sk

    def __skill_is_ready(self, sk: str) -> bool:
        if sk in ['atk', 'auto_button']:
            return True
        return self.objects[sk].found(False)

    def __action_cd_skill(self, sk: str) -> bool:
        # success use skill: True, Fail to use skill: False
        if not self.objects[f'{sk}_cd'].found(False):
            return False
        logger.debug(f'character action: try to click {sk} 0.6 sec (skill cd now?)')
        self.objects[sk].click_sec(0.6, 0.13)
        if self.ready(True):
            return False
        return True

    def __action_auto_button(self):
        adb_update_cache = False
        while not self.objects['auto_button'].found(adb_update_cache):
            self.objects['auto_button'].click(1, 0.5)
            adb_update_cache = True
        self.objects['center'].click(2)

    def __action_sp(self):
        self.objects['sp'].click(1, 0.5)
        self.objects['sp_ch1'].click(1, 0.5)
        self.objects['sp_submit'].click(2)
        self.objects['sp_cancel'].click()  # play safe
        self.objects['center'].click_sec(self.sp_sleep, 0.5)

    def adb_mode_switch(self):
        self.objects = Load_Objects("character")
