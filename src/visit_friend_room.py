import logging
import threading
from typeguard import typechecked
from time import sleep
from run import kirafan


def run(window):
    bot = threading.currentThread()
    bot.send_event = window.write_event_value
    logging.info('visit_friend start...')
    tries = 0
    while bot.is_running():
        if tries == 3:
            bot.stop()
        elif _handle_visit_room(bot, tries, _handle_friend_icon(tries)):
            tries += 1
            logging.info(f'visit_friend time = {tries} success')
            sleep(kirafan.sleep['loading'])

    logging.info('kirafan stop(visit_friend_room)...')
    if bot.is_not_gui_button_stop():
        bot.send_event('_update_button_friend_start_', 'Visit Room')


@typechecked
def _handle_friend_icon(tries: int) -> bool:
    sec = 2 if tries == 0 else 5
    friend_icon_retry = True
    while True:
        if kirafan.icons['ok'].click(2):
            logging.debug('_handle_friend_icon(): click ok button (poor internet connection)')
            sleep(2)
        elif kirafan.icons['friend_icon'].scan(sec):
            kirafan.icons['friend_icon'].click(2, adb_update_cache=False)
            sleep(2)
            return True
        elif tries != 0 and friend_icon_retry:
            logging.debug('try a again because friend_icon.png not found')
            friend_icon_retry = False
        else:
            return False


@typechecked
def _handle_visit_room(bot, tries: int, found_friend_icon: bool) -> bool:
    sec, visit_room_retry = (2, False) if tries == 0 and not found_friend_icon else (5, True)
    while bot.is_running():
        if kirafan.icons['ok'].click(2):
            logging.debug('_handle_visit_room(): click ok button (poor internet connection)')
            sleep(2)
        elif kirafan.icons['visit_room'].scan(sec):
            kirafan.icons['visit_room'].click(2, adb_update_cache=False)
            return True
        elif kirafan.icons['tojiru'].click(adb_update_cache=False):
            logging.error('No friend room....')
            bot.stop()
        elif visit_room_retry:
            logging.debug('try a again because visit_room.png not found')
            visit_room_retry = False
        elif tries == 0:
            logging.error('please move to room!')
            bot.stop()
        else:
            logging.error('unknown error...')
            bot.stop()
    return False
