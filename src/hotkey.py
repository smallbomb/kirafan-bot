import logging
import keyboard
from time import sleep
from typeguard import typechecked
from defined import Tuple
from data import uData
from adb import adb
from thread import Job
from kbhit import KBHit
from window import game_region
from bot import kirafan
from position import Position, Shot, monitor_mode
from run_battle import run as battle


class fake_window:
    def write_event_value(self, *args, **kwargs):
        pass


@typechecked
class Hotkey:
    def __init__(self, keys: str, mode: str = 'hotkey', window=None):
        self.mode = mode
        self.window = window
        self.shot_job = None
        self.battle_job = self.square_job = self.monitor_job = Job()
        self.kb = KBHit()
        self.positions = [Position(_id) for _id in range(1, 10)]
        self.keys = [f'z+{i}' for i in (list(range(1, 10)) if mode == 'hotkey' else []) + list(keys)]
        self.add_hotkey()

    def __user_command(self, key):
        while self.kb.kbhit():
            self.kb.getch()
        if '1' <= key <= '9':
            self.positions[int(key) - 1].record(self.monitor_job.is_alive())
        elif self.monitor_job.is_alive():
            pass
        else:
            self.__call(key)

    def __call(self, key: str):
        method_name = f'_Hotkey__cmd_{key}'
        getattr(self, method_name)()

    def __cmd_r(self):
        if not self.battle_job.is_alive():
            logging.info('press start now!')
            self.battle_job = Job(target=battle, args=(fake_window,))
            self.battle_job.start()
        elif self.battle_job.is_pausing():
            logging.info('press resume now!')
            self.battle_job.resume()

    def __cmd_s(self):
        if self.mode == 'gui':
            if self.window['_button_Start_'].GetText() == 'Stop':
                self.window.write_event_value('_button_Start_', None)
            elif self.window['_button_Visit Room_'].GetText() == 'Stop Visit':
                self.window.write_event_value('_button_Visit Room_', None)
            elif self.window['_button_Cork Shop_'].GetText() == 'Stop Exchange':
                self.window.write_event_value('_button_Cork Shop_', None)
        elif self.battle_job.is_alive():
            logging.info('press stop now!, Please wait for a while')
            self.battle_job.stop()
            self.battle_job.join()

    def __cmd_l(self):
        uData.reload()
        adb.reload()
        kirafan.reload()
        logging.info(f'kirafan region = {list(kirafan.region)}')
        logging.info('reload setting.json finish')
        logging.info(f'kirafan adb use = {uData.setting["adb"]["use"]}')
        logging.info(f'kirafan quest setting = \x1b[41m{kirafan.quest_name}\x1b[0m')

    def __cmd_k(self):
        uData.adb_mode_switch()
        adb.reload()
        kirafan.adb_mode_switch()
        logging.info(f'kirafan region = {list(kirafan.region)}')
        logging.info(f'kirafan adb use = \x1b[35m{uData.setting["adb"]["use"]}\x1b[0m')
        tuple_files = kirafan.miss_icon_files()
        if tuple_files:
            print('miss icon files:')
            for tuple_file in tuple_files:
                print(f'  {tuple_file[1]}')
            print('you can press hotkey "z+c" to add a miss icon file')

    def __cmd_m(self):
        if not self.monitor_job.is_alive():
            self.monitor_job = Job(target=monitor_mode)
            self.monitor_job.start()

    def __cmd_p(self):
        for position in self.positions:
            print(position, end='')

    def __cmd_t(self):
        print('')
        adb.set_update_cv2_IM_cache_flag()
        kirafan.objects_found_all_print()
        kirafan.icons_found_all_print()
        print('')

    def __cmd_c(self):
        if self.shot_job and self.shot_job.is_alive():
            return

        tuple_files = kirafan.miss_icon_files()
        if tuple_files:
            print('miss icon files:')
            for i, tuple_file in enumerate(tuple_files):
                print(f'  {i}.{tuple_file[0]}')

            sleep(0.1)
            if self.kb.kbhit():
                self.kb.getch()

            number = input('select a number which you want to save icon: ')
            if number.isnumeric() and 0 <= int(number) < len(tuple_files):
                self.shot_job = Job(target=self.tutorial_screenshot, args=[tuple_files[int(number)]])
                self.shot_job.start()
            else:
                print('invaild input:', number)
        else:
            print('No miss icon file')

    def __cmd_o(self):
        kirafan.stop_once = not kirafan.stop_once
        logging.info(f'({str(kirafan.stop_once):>5}) kirafan-bot stop after current battle is completed')

    def __cmd_x(self):
        old = uData.setting['game_region'][:2]
        new = game_region()
        if old != new:
            uData.save_location(*new)
            self.__cmd_l()

    def add_hotkey(self):
        for key in self.keys:
            keyboard.add_hotkey(key, self.__user_command, args=[key[-1]])

    def remove_all_hotkey(self):
        for key in self.keys:
            keyboard.remove_hotkey(key)

    def tutorial_screenshot(self, tuple_f: Tuple[str, str]):
        """
        tuple_f = (fname, fpath)
        """
        print(f'Missing {tuple_f[0]} picture')
        print(f'move mouse to the {tuple_f[0]} top left corner, then press hotkey "z+3"')
        keyboard.wait('z+3')
        print(f'move mouse to the {tuple_f[0]} bottom right corner, then press hotkey "z+4"')
        keyboard.wait('z+4')
        Shot(tuple_f[0], tuple_f[1], self.positions[2].coord, self.positions[3].coord).screenshot()

    def wait(self, hotkey: str):
        return keyboard.wait(hotkey)

    def safe_exit(self):
        if self.battle_job.is_alive():
            self.battle_job.stop()
            self.battle_job.join()
        if self.monitor_job.is_alive():
            self.monitor_job.stop()
            self.monitor_job.join()

        sleep(0.1)
        while self.kb.kbhit():
            self.kb.getch()
        print('goodbye!')
