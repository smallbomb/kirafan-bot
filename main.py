import keyboard
from log import logging
from time import sleep
from thread import Job
from data import uData
from kbhit import KBHit
from defined import Region, Tuple
from typeguard import typechecked
from position import Position, Shot, calc_region, monitor_mode
from run import run, kirafan
from window import square


@typechecked
def tutorial_region() -> Region:
    print('drawing game region on window: start')
    print('move mouse to the kirafan screen top left corner, then press hotkey "z+1"')
    keyboard.wait('z+1')
    print('move mouse to the kirafan screen bottom right corner, then press hotkey "z+2"')
    keyboard.wait('z+2')
    print('drawing game region on window: stop')
    return calc_region(positions[0].coord, positions[1].coord)


@typechecked
def tutorial_screenshot(tuple_f: Tuple[str, str]):
    """
    tuple_f = (fname, fpath)
    """
    print('Missing %s picture' % tuple_f[0])
    print('move mouse to the %s top left corner, then press hotkey "z+3"' % tuple_f[0])
    keyboard.wait('z+3')
    print('move mouse to the %s bottom right corner, then press hotkey "z+4"' % tuple_f[0])
    keyboard.wait('z+4')
    Shot(tuple_f[0], tuple_f[1], positions[2].coord, positions[3].coord).screenshot()


main_job = shot_job = monitor_job = square_job = None
kb = KBHit()
positions = [Position(_id) for _id in range(1, 10)]


@typechecked
class Command:
    def call(self, attr_name: str):
        method_name = '_Command__cmd_%s' % attr_name
        getattr(self, method_name)()

    def __cmd_r(self):
        global main_job
        if main_job is None:
            main_job = Job(target=run)
            main_job.set_timer(uData.setting['set_timer'])
            main_job.start()
        else:
            logging.info('press resume now!')
            main_job.resume()

    def __cmd_s(self):
        global main_job
        if main_job:
            logging.info('press stop now!, Please wait for a while')
            main_job.stop()
            main_job.join()
            main_job = None

    def __cmd_l(self):
        uData.reload()
        kirafan.reload()
        logging.info('kirafan region = {}'.format(list(kirafan.region)))
        logging.info('reload setting.json finish')

    def __cmd_m(self):
        global monitor_job
        if monitor_job is None or not monitor_job.is_alive():
            monitor_job = Job(target=monitor_mode)
            monitor_job.start()

    def __cmd_p(self):
        for position in positions:
            print(position, end='')

    def __cmd_t(self):
        print('')
        kirafan.objects_found_all()
        kirafan.icons_found_all()
        print('')

    def __cmd_c(self):
        global shot_job
        if shot_job and shot_job.is_alive():
            return

        tuple_files = kirafan.miss_icon_files()
        if tuple_files:
            print('miss icon files:')
            for i, tuple_file in enumerate(tuple_files):
                print('  {}.{}'.format(i, tuple_file[0]))

            sleep(0.1)
            if kb.kbhit():
                kb.getch()

            number = input('select a number which you want to save icon: ')
            if number.isnumeric() and 0 <= int(number) < len(tuple_files):
                shot_job = Job(target=tutorial_screenshot, args=[tuple_files[int(number)]])
                shot_job.start()
            else:
                print('invaild input:', number)
        else:
            print('No miss icon file')

    def __cmd_x(self):
        global square_job
        if square_job is None or not square_job.is_alive():
            square_job = Job(target=square)
            square_job.start()
        else:
            square_job.stop()
            square_job.join()
            square_job = None


cmd = Command()


@typechecked
def user_command(key: str):
    while kb.kbhit():
        kb.getch()
    if '1' <= key <= '9':
        positions[int(key) - 1].record(bool(monitor_job) and monitor_job.is_alive())
    elif monitor_job and monitor_job.is_alive():
        pass
    else:
        cmd.call(key)


def _init():
    keys = ['z+{}'.format(i) for i in (list(range(1, 10)) + list('rslmptcx'))]
    for key in keys:
        keyboard.add_hotkey(key, user_command, args=[key[-1]])
    logging.info("hotkey setting finish...")

    if uData.region_is_init():
        uData.setting['game_region'] = tutorial_region()
        kirafan.reload()
    logging.info('kirafan region = {}'.format(list(kirafan.region)))

    tuple_files = kirafan.miss_icon_files()
    if tuple_files:
        print('miss icon files:')
        for tuple_file in tuple_files:
            print('  {}'.format(tuple_file[1]))
        print('you can press hotkey "z+c" to add a miss icon file')


def safe_exit():
    if main_job and main_job.is_alive():
        main_job.stop()
        main_job.join()
    if monitor_job and monitor_job.is_alive():
        monitor_job.stop()
        monitor_job.join()
    if square_job and square_job.is_alive():
        square_job.stop()
        square_job.join()
    sleep(0.1)
    while kb.kbhit():
        kb.getch()
    print("goodbye!")


if __name__ == '__main__':
    try:
        _init()
        print('please press \'q\' button to exit...')
        keyboard.wait('q')
        safe_exit()
    except KeyboardInterrupt:
        safe_exit()
