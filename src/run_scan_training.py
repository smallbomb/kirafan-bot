import threading
from log import logger
from data import uData
from time import sleep
from bot import kirafan


def run(window):
    bot = threading.currentThread()
    bot.send_event = lambda event, value: bot.is_not_gui_button_stop() and window.write_event_value(event, value)
    if kirafan.icons['training_icon'].click():
        _sleep(bot, 5)
    elif kirafan.icons['menu'].scan_then_click(scan_timeout=5):
        kirafan.icons['training_icon'].scan_then_click(scan_timeout=3)
        _sleep(bot, 5)
    else:
        logger.error('unknown place...?')
        bot.stop()

    while bot.is_running():
        logger.info(f"scan training start...(checking every {kirafan.sleep['scan_training']}s)")
        if kirafan.objects['scan_training_button'].found():
            kirafan.objects['scan_training_button'].click(2)
            logger.info('run_scan_training(): click training finish button')
            _sleep(bot, 2)
            _bulk_challenge(bot)
        elif _ck_session_clear_text_and_resume(bot):
            continue
        elif kirafan.icons['ok'].click(2, adb_update_cache=False):
            logger.debug('run_scan_training(): click ok button (poor internet connection)')
            _sleep(bot, 2)
        elif uData.setting["adb"]["use"] and kirafan.detect_crashes():
            _scan_training_resume(bot)
        _sleep(bot, kirafan.sleep['scan_training'])

    logger.info('kirafan-bot stop(scan training)...')
    bot.send_event('_update_button_scan_training_', 'Scan Training')


def _sleep(bot, sec: float):
    while bot.is_running() and sec > 0:
        sleep(1)
        sec -= 1


def _bulk_challenge(bot):
    tries = 3
    while bot.is_running():
        if tries <= 0:
            logger.debug('_bulk_challenge(): bulk_challenge.png not found')
            break
        if kirafan.icons['bulk_challenge'].scan_then_click(scan_timeout=3):
            logger.debug('_bulk_challenge(): click bulk challenge button')
            _sleep(bot, 2)
            break
        elif _ck_session_clear_text_and_resume(bot):
            break
        elif kirafan.icons['ok'].click(2, adb_update_cache=False):
            logger.debug('bulk_challenge(): click ok button (poor internet connection)')
            _sleep(bot, 2)
        tries -= 1
        _sleep(bot, 1)


def _ck_session_clear_text_and_resume(bot):
    if kirafan.icons['session_clear_text'].found(False):
        logger.debug('_ck_session_clear_text_and_resume(): session_clear_text.png found')
        kirafan.icons['ok'].click(2, adb_update_cache=False)
        _scan_training_resume(bot)
        return True
    return False


def _scan_training_resume(bot):
    logger.warning('_scan_training_resume(): try to scan training...')
    kirafan.objects['center'].click_sec(100)
    while kirafan.icons['ok'].click():
        _sleep(bot, 2)
    kirafan.icons['X'].click(adb_update_cache=False)
    kirafan.icons['menu'].scan_then_click(scan_timeout=3)
    if kirafan.icons['training_icon'].scan_then_click(scan_timeout=3):
        logger.info('_scan_training_resume(): resume to scan training success')
        _sleep(bot, 5)
    else:
        logger.error('_scan_training_resume(): resume to scan training failed')
        bot.stop()
