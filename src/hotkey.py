import logging
import keyboard
from time import sleep
from typeguard import typechecked
from defined import Region, Tuple
from data import uData
from thread import Job
from kbhit import KBHit
from window import square
from run import run, kirafan
from position import Position, Shot, calc_region, monitor_mode


@typechecked
class Hotkey:
    def __init__(self, keys: str):
        self.shot_job = None
        self.run_job = Job(target=run)
        self.square_job = Job(target=square)
        self.monitor_job = Job(target=monitor_mode)
        self.kb = KBHit()
        self.positions = [Position(_id) for _id in range(1, 10)]
        self.keys = ['z+{}'.format(i) for i in (list(range(1, 10)) + list(keys))]
        for key in self.keys:
            keyboard.add_hotkey(key, self.__user_command, args=[key[-1]])

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
        method_name = '_Hotkey__cmd_%s' % key
        getattr(self, method_name)()

    def __cmd_r(self):
        if not self.run_job.is_alive():
            logging.info('press start now!')
            self.run_job = Job(target=run)
            self.run_job.start()
        elif self.run_job.is_pausing():
            logging.info('press resume now!')
            self.run_job.resume()

    def __cmd_s(self):
        if self.run_job.is_alive():
            logging.info('press stop now!, Please wait for a while')
            self.run_job.stop()
            self.run_job.join()

    def __cmd_l(self):
        uData.reload()
        kirafan.reload()
        logging.info('kirafan region = {}'.format(list(kirafan.region)))
        logging.info('reload setting.json finish')
        logging.info('kirafan quest setting = \x1b[41m{}\x1b[0m'.format(kirafan.quest_name))

    def __cmd_m(self):
        if not self.monitor_job.is_alive():
            self.monitor_job = Job(target=monitor_mode)
            self.monitor_job.start()

    def __cmd_p(self):
        for position in self.positions:
            print(position, end='')

    def __cmd_t(self):
        print('')
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
                print('  {}.{}'.format(i, tuple_file[0]))

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
        logging.info('(%5s) kirafan-bot stop after current battle is completed' % str(kirafan.stop_once))

    def __cmd_x(self):
        if self.square_job.is_alive():
            self.square_job.stop()
            self.square_job.join()
        else:
            self.square_job = Job(target=square)
            self.square_job.start()

    def tutorial_region(self) -> Region:
        print('drawing game region on window: start')
        print('move mouse to the kirafan screen top left corner, then press hotkey "z+1"')
        keyboard.wait('z+1')
        print('move mouse to the kirafan screen bottom right corner, then press hotkey "z+2"')
        keyboard.wait('z+2')
        print('drawing game region on window: stop')
        return calc_region(self.positions[0].coord, self.positions[1].coord)

    def tutorial_screenshot(self, tuple_f: Tuple[str, str]):
        """
        tuple_f = (fname, fpath)
        """
        print('Missing %s picture' % tuple_f[0])
        print('move mouse to the %s top left corner, then press hotkey "z+3"' % tuple_f[0])
        keyboard.wait('z+3')
        print('move mouse to the %s bottom right corner, then press hotkey "z+4"' % tuple_f[0])
        keyboard.wait('z+4')
        Shot(tuple_f[0], tuple_f[1], self.positions[2].coord, self.positions[3].coord).screenshot()

    def wait(self, hotkey: str):
        return keyboard.wait(hotkey)

    def safe_exit(self):
        if self.run_job.is_alive():
            self.run_job.stop()
            self.run_job.join()
        if self.monitor_job.is_alive():
            self.monitor_job.stop()
            self.monitor_job.join()
        if self.square_job.is_alive():
            self.square_job.stop()
            self.square_job.join()

        sleep(0.1)
        while self.kb.kbhit():
            self.kb.getch()
        print("goodbye!")
