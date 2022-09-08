'''
For backup
not implement on gui

if you want to use this feature(auto gacha), copy code and paste to 'run_cork_shop_exchange.py' (replace code)
then, click cork shop button on gui.
'''


import threading
from log import logger
from bot import kirafan
from time import sleep


def run(window):
    bot = threading.currentThread()
    bot.send_event = lambda event, value: bot.is_not_gui_button_stop() and window.write_event_value(event, value)
    gacha_limit = 100
    logger.info(f'start gacha {gacha_limit} times...')
    time = 1
    '''
    單抽按鈕
    ↓
    確認
    ↓
    點center
    ↓
    確認5星?
    ↓
    閉じる按鈕
    ↓
    loop start
    '''
    while bot.is_running():
        if time > gacha_limit:
            bot.stop()
            break
        if kirafan.icons['gacha'].scan_then_click(scan_timeout=5) and kirafan.icons['hai'].scan_then_click(scan_timeout=5):
            sleep(2)
            if kirafan.icons['hai'].scan_then_click(scan_timeout=9):
                logger.info(f'gacha {time}')
                if kirafan.icons['gacha_clea'].scan_then_click(scan_timeout=15):
                    sleep(15)
                    kirafan.screenshot()
                    kirafan.objects['center'].click()
                    sleep(2)
                    kirafan.objects['center'].click()
                    sleep(3)
                    if not kirafan.icons['tojiru'].scan_then_click(scan_timeout=3):
                        bot.stop()
                        break
                    sleep(2)
                    kirafan.icons['tojiru'].scan_then_click(scan_timeout=5)
                    sleep(4)
        else:
            kirafan.objects['center'].click()
            sleep(3)
            continue
        time += 1

    logger.info('kirafan-bot stop(gacha)...')
    bot.send_event('_update_button_cork_shop_', 'Cork Shop')
