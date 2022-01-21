from log import logging
from data import uData
from run import kirafan
from hotkey import Hotkey
from gui import kirafanbot_GUI
# from thread import Job
# from time import sleep


# def hotkey_wait_for_gui(stop):
#     while True:
#         sleep(1)
#         if stop():
#             break

def check_basic_information(hotkey):
    if uData.region_is_init():
        uData.setting['game_region'] = hotkey.tutorial_region()
        kirafan.reload()
    logging.info(f'kirafan region = {list(kirafan.region)}')
    logging.info(f'kirafan adb use = {uData.setting["adb"]["use"]}')
    logging.info(f'kirafan quest setting = \x1b[41m{kirafan.quest_name}\x1b[0m')

    tuple_files = kirafan.miss_icon_files()
    if tuple_files:
        print('miss icon files:')
        for tuple_file in tuple_files:
            print(f'  {tuple_file[1]}')
        print('you can press hotkey "z+c" to add a miss icon file')


def main():
    if uData.setting['mode'].lower() == 'gui':
        kirafanbot_GUI().open()
        # Hotkey('s', mode='gui', window=gui.window)
        # stop_thread = False
        # Job(target=hotkey_wait_for_gui, args=(lambda: stop_thread,)).start()
        # gui.open()
        # stop_thread = True

    elif uData.setting['mode'].lower() == 'hotkey':
        try:
            hotkey = Hotkey('rslmptcoxk')
            logging.info("hotkey setting finish...")
            check_basic_information(hotkey)
            print('please press \'f3\' button to exit...')
            hotkey.wait('f3')
            hotkey.safe_exit()
        except KeyboardInterrupt:
            hotkey.safe_exit()


if __name__ == '__main__':
    main()
