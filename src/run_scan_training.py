import threading
from log import logger
from time import sleep
from bot import kirafan


def run(window):
    bot = threading.currentThread()
    bot.send_event = lambda event, value: bot.is_not_gui_button_stop() and window.write_event_value(event, value)
    logger.info(f"scan training start...(checking every {kirafan.sleep['scan_training']}s)")
    while bot.is_running():
        if kirafan.objects['scan_training_button'].found():
            kirafan.objects['scan_training_button'].click()
            logger.info('click training finish button')
            sleep(2)
            bulk_challenge()
        elif kirafan.icons['ok'].click(2, adb_update_cache=False):
            logger.debug('run_scan_training(): click ok button (poor internet connection)')
            sleep(2)
        sleep(kirafan.sleep['scan_training'])
    logger.info('kirafan-bot stop(scan training)...')
    bot.send_event('_update_button_scan_training_', 'Visit Room')


def bulk_challenge(bot):
    tries = 3
    while bot.is_running():
        if tries < 0:
            logger.error('bulk_challenge(): bulk_challenge.png not found')
            break
        if kirafan.icons['bulk_challenge'].scan_then_click(scan_timeout=3):
            logger.debug('click bulk challenge button')
            sleep(2)
            break
        elif kirafan.icons['ok'].click(2, adb_update_cache=False):
            logger.debug('bulk_challenge(): click ok button (poor internet connection)')
            sleep(2)
        tries -= 1
        sleep(1)
