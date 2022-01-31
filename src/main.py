from log import logger
from data import uData
from bot import kirafan
from hotkey import Hotkey
from gui import kirafanbot_GUI


def check_basic_information():
    tuple_files = kirafan.miss_icon_files()
    if tuple_files:
        print('miss icon files:')
        for tuple_file in tuple_files:
            print(f'  {tuple_file[1]}')
        print('you can press hotkey "z+c" to add a miss icon file')


def main():
    if uData.setting['mode'].lower() == 'gui':
        kirafanbot_GUI().open()
    elif uData.setting['mode'].lower() == 'hotkey':
        try:
            hotkey = Hotkey('rslmptcoxkvei')
            logger.info("kirafan-bot: hotkey setting finish...")
            logger.info(f'kirafan-bot: region = {list(kirafan.region)}')
            logger.info(f'kirafan-bot: adb use = {uData.setting["adb"]["use"]}')
            logger.info(f'kirafan-bot: quest setting = \x1b[41m{kirafan.quest_name}\x1b[0m')
            check_basic_information()
            logger.info('please press \'f3\' button to exit...')
            hotkey.wait('f3')
            hotkey.safe_exit()
        except KeyboardInterrupt:
            hotkey.safe_exit()


if __name__ == '__main__':
    main()
