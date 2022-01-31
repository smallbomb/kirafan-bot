import threading
from log import logger
from bot import kirafan


def run(window):
    bot = threading.currentThread()
    bot.send_event = lambda event, value: bot.is_not_gui_button_stop() and window.write_event_value(event, value)
    logger.info('cork shop start...')
    time = 1
    while bot.is_running():
        if kirafan.icons['cork_face'].scan(3):
            if kirafan.objects['shop_enhance_field'].found(False) or kirafan.objects['shop_evo_field'].found(False):
                if kirafan.cork_shop_exchange_once(lambda: not bot.is_running()):
                    logger.debug(f'cork shop: {time} times success')
                    time += 1
                    continue
            else:
                logger.error('please select \'強化素材\' or \'進化素材\'!')
        else:
            logger.error('please move to cork shop!')
        bot.stop()

    logger.info('kirafan-bot stop(cork shop)...')
    bot.send_event('_update_button_cork_shop_', 'Cork Shop')
