from log import logging
from data import uData
from run import kirafan
from hotkey import Hotkey


def check_basic_information(hotkey):
    if uData.region_is_init():
        uData.setting['game_region'] = hotkey.tutorial_region()
        kirafan.reload()
    logging.info(f'kirafan region = {list(kirafan.region)}'.format())
    logging.info(f'kirafan quest setting = \x1b[41m{kirafan.quest_name}\x1b[0m')

    tuple_files = kirafan.miss_icon_files()
    if tuple_files:
        print('miss icon files:')
        for tuple_file in tuple_files:
            print(f'  {tuple_file[1]}')
        print('you can press hotkey "z+c" to add a miss icon file')


def main():
    try:
        hotkey = Hotkey('rslmptcox')
        logging.info("hotkey setting finish...")
        check_basic_information(hotkey)
        print('please press \'q\' button to exit...')
        hotkey.wait('q')
        hotkey.safe_exit()
    except KeyboardInterrupt:
        hotkey.safe_exit()


if __name__ == '__main__':
    main()
