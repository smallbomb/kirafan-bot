import threading
from log import logger
from data import uData
from bot import kirafan
from adb import adb


def run(window):
    bot = threading.currentThread()
    bot.send_event = lambda event, value: bot.is_not_gui_button_stop() and window.write_event_value(event, value)
    logger.info(f"scan training start...(check button every {kirafan.sleep['scan_training']}s)")
    _try_to_move_training(bot)
    bot.is_running() and logger.debug('run_scan_training(): move training place success')
    while bot.is_running():
        _ck_session_timer(bot)
        if kirafan.objects['scan_training_button'].found():
            kirafan.objects['scan_training_button'].click(2)
            logger.info('run_scan_training(): click training finish button')
            _bulk_challenge(bot)
        elif kirafan.icons['bulk_challenge'].found(adb_update_cache=False):
            logger.warning('run_scan_training(): retry bulk_challenge')
            _bulk_challenge(bot)
        elif _ck_session_clear_text_and_resume(bot):
            continue
        elif kirafan.icons['ok'].click(2, adb_update_cache=False):
            logger.debug('run_scan_training(): click ok button (poor internet connection)')
            kirafan.break_sleep(2, lambda: not bot.is_running())
        elif uData.setting["adb"]["use"] and kirafan.detect_crashes():
            _scan_training_resume(bot)
        kirafan.break_sleep(kirafan.sleep['scan_training'], lambda: not bot.is_running())

    logger.info('kirafan-bot stop(scan training)...')
    bot.send_event('_update_button_scan_training_', 'Scan Training')


def _try_to_move_training(bot):
    kirafan.icons['X'].click()
    if kirafan.icons['training_icon'].click():
        kirafan.break_sleep(5, lambda: not bot.is_running())
    elif kirafan.icons['menu'].scan_then_click(scan_timeout=5):
        kirafan.icons['training_icon'].scan_then_click(scan_timeout=3)
        kirafan.break_sleep(5, lambda: not bot.is_running())
    elif uData.setting["adb"]["use"] and kirafan.detect_crashes():
        _scan_training_resume(bot)
    else:
        logger.error('unknown place...?')
        bot.stop()


def _ck_session_timer(bot):
    if uData.setting["adb"]["use"] and kirafan.ck_timer_pause(lambda: not bot.is_running(), lambda s: bot.send_event('_timer_countdown_', s), run_mode='scan_training') and bot.is_running():  # noqa: E501
        logger.info('run_scan_training(): restart kirafan app beacause session timer is up.')
        adb.restart_app()
        _scan_training_resume(bot)


def _bulk_challenge(bot):
    tries = 3
    while bot.is_running():
        if tries <= 0:
            logger.debug('_bulk_challenge(): bulk_challenge.png not found')
            break
        if tries == 3 and kirafan.icons['nakayoshido'].scan(2):
            kirafan.objects['nakayoshido_tojiru'].click(2)
            continue
        elif tries == 3 and kirafan.icons['iie'].click(adb_update_cache=False):
            continue
        if kirafan.icons['bulk_challenge'].scan_then_click(scan_timeout=3):
            logger.debug('_bulk_challenge(): click bulk challenge button')
            kirafan.break_sleep(2, lambda: not bot.is_running())
            break
        elif _ck_session_clear_text_and_resume(bot):
            break
        elif kirafan.icons['ok'].click(2, adb_update_cache=False):
            logger.debug('bulk_challenge(): click ok button (poor internet connection)')
            kirafan.break_sleep(2, lambda: not bot.is_running())
            continue
        tries -= 1
        kirafan.break_sleep(1, lambda: not bot.is_running())


def _ck_session_clear_text_and_resume(bot):
    if kirafan.icons['session_clear_text'].found(False):
        logger.debug('_ck_session_clear_text_and_resume(): session_clear_text.png found')
        kirafan.icons['ok'].click(2, adb_update_cache=False)
        _scan_training_resume(bot)
        return True
    return False


def _scan_training_resume(bot):
    logger.warning('_scan_training_resume(): try to resume to training place...')
    kirafan.objects['center'].click_sec(100, interrupt=lambda: not bot.is_running())
    if not bot.is_running():
        return
    while kirafan.icons['ok'].click():
        kirafan.break_sleep(2, lambda: not bot.is_running())
    kirafan.icons['X'].click(adb_update_cache=False)
    kirafan.icons['menu'].scan_then_click(scan_timeout=3)
    if kirafan.icons['training_icon'].scan_then_click(scan_timeout=3):
        logger.info('_scan_training_resume(): resume to scan training success')
        kirafan.break_sleep(5, lambda: not bot.is_running())
    else:
        logger.error('_scan_training_resume(): resume to scan training failed')
        bot.stop()
