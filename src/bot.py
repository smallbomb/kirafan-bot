import logging
from typeguard import typechecked
from defined import Optional, Tuple, Dict
from data import uData
from wave import Wave, gen_circle_list
from icon import Icon
from object import Load_Objects
from time import sleep
from datetime import datetime, timedelta


@typechecked
def wait_until(time: datetime):
    def to_hour(s: float) -> int:
        return int(s / 3600) % 24

    def to_min(s: float) -> str:
        return int(s / 60) % 60

    def to_sec(s: float) -> int:
        return int(s) % 60

    log_t = datetime.fromtimestamp(0)
    while True:
        now_time = datetime.now()
        wait_s = round((time - now_time).total_seconds(), 1)
        if wait_s < 0:
            break
        if (now_time - log_t).total_seconds() > 60:
            s = '倒數: {:02d}時 {:02d}分 {:02d}秒, 現在時間: {:s} 結束暫停時間: {:s}'
            logging.info(s.format(to_hour(wait_s), to_min(wait_s), to_sec(wait_s),
                                  now_time.strftime("%H:%M:%S"), time.strftime("%H:%M:%S")))
            log_t = now_time
        sleep(wait_s / 2)


@typechecked
class BOT:
    def __init__(self):
        self.wave_id = -1
        self.wave_change_flag = None
        self.stop_once = False
        self.data = uData.setting
        self.region = self.data['game_region']
        self.quest_name = self.data['quest_selector']
        self.wave_total = self.data['wave']['total']
        self.loop_count = self.data['loop_count']
        self.sleep = self.data['sleep']
        self.crea_stop = self.data['crea_stop']
        self.stamina = self.data['stamina'] or {"use": False}
        self.objects = Load_Objects("bot")
        self.icons = self.__load_icons()
        self.waves = self.__load_waves()
        self.__timer = self.data['set_timer']['pause_range'] if self.data['set_timer']['use'] else None
        self.__ck_crash_count = 0

    def __str__(self) -> str:
        string = str(self.__class__) + ":\n"
        for item in self.__dict__:
            if item in ['objects', 'icons', 'waves']:
                for value in self.__dict__[item].values():
                    string += item + str(value) + "\n"
            else:
                string += "{} = {}\n\n".format(item, self.__dict__[item])
        return string

    def __load_icons(self) -> Dict:
        images = ['kirara_face.png', 'kuromon.png', 'ok.png', 'hai.png', 'tojiru.png']
        if self.stamina['use']:
            images += ['stamina_Au.png']
        if self.loop_count > 0:
            images += ['again.png']
        if self.data['crash_detection']:
            images += ['kirara_game_icon.png', 'start_screen.png']
        icons = [Icon(image, self.data['common_confidence']) for image in images]
        return {icon.name: icon for icon in icons}

    def __load_waves(self) -> Dict:
        return {str(wave_id): Wave(wave_id, self.wave_total)
                for wave_id in range(1, self.wave_total + 1)}

    def __update_value(self, new_waveid: int):
        '''wave id was found and then update some value.
        '''
        if self.wave_id != new_waveid:
            # wave id will be changed
            self.wave_change_flag = True
            self.waves[str(new_waveid)].reset()
            if new_waveid < self.wave_id:
                # is new battle
                self.stop_once = False
        else:
            self.wave_change_flag = False

        # crash count reset
        self.__ck_crash_count = 0
        self.wave_id = new_waveid

    def update_waveID(self) -> bool:
        for new_wid in gen_circle_list(self.wave_id, self.wave_total):
            if self.waves[str(new_wid)].current():
                self.__update_value(new_wid)
                return True
        return False

    def get_current_wave(self) -> Optional[Wave]:
        return self.waves[str(self.wave_id)]

    def use_stamina(self) -> bool:
        for s in self.stamina['priority']:
            if self.objects['stamina_{}'.format(s)].found():
                self.objects['stamina_{}'.format(s)].click(2, 0.5)
                if self.stamina['count'] > 1:
                    self.objects['stamina_add'].click(self.stamina['count'] - 1)
                self.objects['stamina_hai'].click(8)
                return True
        return False

    def miss_icon_files(self) -> Tuple:
        ret = tuple()
        for wave in self.waves.values():
            if not wave.icon.file_exist():
                ret += (wave.icon.name, wave.icon.path)
        for icon in self.icons.values():
            if not icon.file_exist():
                ret += (icon.name, icon.path)
        return tuple(zip(ret[0::2], ret[1::2]))

    def objects_found_all_print(self):
        print("objects found:")
        for object in Load_Objects('all').values():
            print(f'  {object.name:16} {object.found()}')

    def icons_found_all_print(self):
        print("icons found:")
        for icon in self.icons.values():
            print(f'  {icon.name:16} {icon.get_center()}')
        for wave in self.waves.values():
            print(f'  {wave.name:16} {wave.get_icon_coord()}')

    def detect_crashes(self) -> bool:
        self.__ck_crash_count += 1
        if self.data['crash_detection']:
            if self.__ck_crash_count > 300:  # bot will be stoped.
                return True
            if self.__ck_crash_count > 150:
                self.objects['home_page'].click()
            if self.__ck_crash_count > 100:  # try to move mouse and then click.
                self.objects['center'].click()
            if self.__ck_crash_count > 50:
                self.objects['center_left'].click()
                return self.icons['kirara_game_icon'].click() or self.icons['start_screen'].found()
        return False

    def ck_timer_pause(self) -> bool:
        def time_in_range(start: datetime, end: datetime, now: datetime) -> bool:
            if start <= end:
                return start <= now <= end
            else:
                return start <= now or now <= end

        if self.__timer:
            start_clock, end_clock = self.__timer.split('-')
            start_time = datetime.strptime(str(datetime.now().date()) + "T" + start_clock, "%Y-%m-%dT%H:%M:%S")
            end_time = datetime.strptime(str(datetime.now().date()) + "T" + end_clock, "%Y-%m-%dT%H:%M:%S")
            now_time = datetime.now()
            if time_in_range(start_time, end_time, datetime.now()):
                self.objects['center'].click(3)  # advoid auto mode
                wait_until(end_time if end_time >= now_time else end_time + timedelta(days=1))
                return True
        return False

    def reload(self):
        # self.wave_id = -1
        # self.wave_change_flag = None
        self.stop_once = False
        self.data = uData.setting
        self.region = self.data['game_region']
        self.quest_name = self.data['quest_selector']
        self.wave_total = self.data['wave']['total']
        self.loop_count = self.data['loop_count']
        self.sleep = self.data['sleep']
        self.crea_stop = self.data['crea_stop']
        self.stamina = self.data['stamina'] or {"use": False}
        self.objects = Load_Objects("bot")
        self.icons = self.__load_icons()
        self.waves = self.__load_waves()
        self.__timer = self.data['set_timer']['pause_range'] if self.data['set_timer']['use'] else None
        self.__ck_crash_count = 0


# Test
if __name__ == '__main__':
    bot = BOT()
    print(bot.miss_icon_files())
