import logging
import threading
from time import sleep
from bot import BOT


kirafan = BOT()


def run(window):
    bot = threading.currentThread()
    bot.send_event = window.write_event_value
    logging.info('visit_friend start...')
    tries = 0
    while bot.is_running():
        if tries == 3:
            bot.stop()
        _handle_friend_icon(bot, tries)
        if _handle_visit_room(bot):
            tries += 1
            logging.info(f'visit_friend time = {tries} success')
            sleep(kirafan.sleep['loading'])

    logging.info('kirafan stop(visit_room)...')
    if bot.is_not_gui_button_stop():
        bot.send_event('_update_button_friend_start_', 'Visit Room')

def _handle_friend_icon(bot, tries):
    sec = 2 if tries == 0 else 5
    friend_icon_retry = True
    while bot.is_running():
        if kirafan.icons['friend_icon'].scan(sec):
            kirafan.icons['friend_icon'].click(2, adb_update_cache=False)
            sleep(2)
            break
        elif friend_icon_retry:
            logging.debug('try a again because friend_icon.png not found')
            friend_icon_retry = False
        else:
            break

def _handle_visit_room(bot) -> bool: 
    visit_room_retry = True
    while bot.is_running():
        if kirafan.icons['visit_room'].scan(5):
            kirafan.icons['visit_room'].click(adb_update_cache=False)
            return True
        elif kirafan.icons['tojiru'].click(adb_update_cache=False):
            logging.error('No friend room....')
            bot.stop()
        elif visit_room_retry:
            logging.debug('try a again because visit_room.png not found')
            visit_room_retry = False
        else:
            logging.error('unknown error...')
            bot.stop()
    return False