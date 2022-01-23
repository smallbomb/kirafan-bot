import logging
import threading
from bot import kirafan


def run(window):
    bot = threading.currentThread()
    bot.send_event = lambda event, value: bot.is_not_gui_button_stop() and window.write_event_value(event, value)
    logging.info('cork shop start...')
    time = 1
    while bot.is_running():
        if kirafan.icons['cork_face'].scan(3):
            if kirafan.objects['shop_enhance_field'].found(False) or kirafan.objects['shop_evo_field'].found(False):
                if kirafan.cork_shop_exchange_once(lambda: not bot.is_running()):
                    logging.debug(f'cork shop {time} times success')
                    time += 1
                    continue
            else:
                logging.error('please select \'強化素材\' or \'進化素材\'!')
        else:
            logging.error('please move to cork shop!')
        bot.stop()

    logging.info('kirafan stop(cork shop)...')
    bot.send_event('_update_button_cork_shop_', 'Cork Shop')
