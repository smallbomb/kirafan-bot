import threading
from log import logger
from typeguard import typechecked
from time import sleep
from bot import kirafan


def run(window):
    bot = threading.currentThread()
    bot.send_event = lambda event, value: bot.is_not_gui_button_stop() and window.write_event_value(event, value)
    logger.info('visit friend start...')
    tries = 0
    while bot.is_running():
        if tries == 3:
            bot.stop()
        elif _handle_visit_room(bot, tries, _handle_friend_icon(tries)):
            tries += 1
            logger.info(f'visit friend room time = {tries} success')
            sleep(kirafan.sleep['loading'])

    logger.info('kirafan-bot stop(visit friend)...')
    bot.send_event('_update_button_visit_room_', 'Visit Room')


@typechecked
def _handle_friend_icon(tries: int) -> bool:
    sec = 2 if tries == 0 else 5
    friend_icon_retry = True
    while True:
        if kirafan.icons['ok'].click(2):
            logger.debug('_handle_friend_icon(): click ok button (poor internet connection)')
            sleep(2)
        elif kirafan.icons['friend_icon'].scan_then_click(scan_timeout=sec, click_times=2):
            sleep(2)
            return True
        elif tries != 0 and friend_icon_retry:
            logger.debug('try a again because friend_icon.png not match on game region')
            friend_icon_retry = False
        else:
            return False


@typechecked
def _handle_visit_room(bot, tries: int, found_friend_icon: bool) -> bool:
    sec, visit_room_retry = (2, False) if tries == 0 and not found_friend_icon else (5, True)
    while bot.is_running():
        if kirafan.icons['ok'].click(2):
            logger.debug('_handle_visit_room(): click ok button (poor internet connection)')
            sleep(2)
        elif kirafan.icons['visit_room'].scan_then_click(scan_timeout=sec, click_times=2):
            return True
        elif visit_room_retry:
            logger.debug('try a again because visit_room.png not match on game region')
            visit_room_retry = False
        elif tries == 0:
            logger.error('please move to room!')
            bot.stop()
        else:
            logger.error('_handle_visit_room(): unknown error...')
            bot.stop()
    return False
