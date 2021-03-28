import logging
import threading
from typeguard import typechecked
from time import sleep
from bot import BOT


kirafan = BOT()


def run():
    bot = threading.currentThread()
    logging.info('kirafan start...')
    logging.info('loop_count = {} now'.format(kirafan.loop_count))
    while bot.is_running():
        if _is_battle_now():
            if kirafan.wave_change_flag:
                logging.info('wave({}/{}) now...'.format(kirafan.wave_id, kirafan.wave_total))
            _handle_battle_flows()
        else:
            # is not battle (maybe transitions, loading, sp animation, crash ... etc)
            if kirafan.detect_crashes():
                logging.warning('detect crashes')
                _battle_resume(bot)
            elif _is_last_wave():
                _handle_award_flows(bot)
            else:
                logging.debug('transitions now...({}/{})'.format(kirafan.wave_id, kirafan.wave_total))
                sleep(kirafan.sleep['wave_transitions'])
    logging.info('kirafan stop...')


@typechecked
def _is_battle_now() -> bool:
    if kirafan.update_waveID():
        return True
    else:
        return False


def _handle_battle_flows():
    wave = kirafan.get_current_wave()

    if wave.auto:
        wave.auto_click()
    elif wave.is_myTurn():
        if wave.update_characterID():
            if wave.friend_action() or wave.orb_action():
                return
            logging.debug('character(%02d) action start' % wave.ch_id)
            wave.charater_action()
            logging.debug('character(%02d) action finish' % wave.ch_id)
        else:
            logging.error('wave-{}/{}: character not found'.format(wave.id, wave.total))
    else:
        kirafan.objects['center'].click_sec(1)


@typechecked
def _is_last_wave() -> bool:
    return kirafan.wave_id >= kirafan.wave_total or kirafan.wave_change_flag is None


def _handle_award_flows(bot):
    '''
    1. kiraraface?
    2. session clear?
    3. loading?
    '''
    if kirafan.icons['kirara_face'].scan(2):
        kirafan.wave_id = kirafan.wave_total + 1  # for wave reset.
        kirafan.loop_count -= 1
        logging.debug("try to move next new battle")
        _try_to_move_next_new_battle(bot)
    elif kirafan.icons['ok'].click():
        _handle_ok_button(bot)
    else:
        logging.debug('still loading now...')
        sleep(1)


def _try_to_move_next_new_battle(bot):
    _skip_award_result(bot)
    while bot.is_running():
        if _ck_move_to_next_battle(bot):
            logging.debug('player is moving to next battle...')
            logging.info('loop_count = {} now'.format(kirafan.loop_count))
            sleep(kirafan.sleep['loading'])
            break
        elif not bot.is_running():
            # insufficient stamina items.
            break
        elif kirafan.icons['ok'].click():
            # if event is session clear, bot will not resume battle. because of batttle finish.
            logging.debug('_try_to_move_next_new_battle(): click ok button (poor internet connection)')
        elif kirafan.stamina['use'] and kirafan.icons['tojiru'].click():
            # disconnection after using stamina
            sleep(0.5)
            kirafan.icons['again'].click()
            logging.debug('_try_to_move_next_new_battle(): click tojiru button (stamina page was not closed)')
        else:
            logging.error('Can not move to next new battle. maybe insufficient stamina items? pause now...')
            bot.pause()
            bot.wait()
            break


def _skip_award_result(bot):
    logging.debug("handle award result page")
    if kirafan.stop_once:
        logging.debug('kirafan-bot.stop_once be setup. (z+o)')
        kirafan.stop_once = False
        bot.stop()
    elif kirafan.loop_count <= 0:
        logging.info('loop_count(%d) less than or equal to 0' % kirafan.loop_count)
        bot.stop()

    ct = 12
    while bot.is_running():
        kirafan.objects['center_left'].click(ct)
        if kirafan.icons['again'].click():
            break
        elif kirafan.crea_stop and kirafan.objects['center_left'].found() and kirafan.icons['tojiru'].found():
            logging.info('crea_stop: appear crea mission')
            bot.stop()
        elif kirafan.icons['tojiru'].click():
            logging.debug('icon: tojiru icon found')
            ct = 8
        else:
            logging.error('icon: again.png not found...')
            bot.stop()


def _ck_move_to_next_battle(bot) -> bool:
    # check stamina_Au first. wait for loading time even if user has enough stamina.
    if kirafan.stamina['use'] and kirafan.icons['stamina_Au'].scan(1.5):
        if not kirafan.use_stamina():
            logging.info('insufficient stamina items.')
            bot.stop()
            return False
        if not kirafan.icons['again'].click():
            return False

    return kirafan.icons['kuromon'].scan(4)


def _battle_resume(bot):
    logging.warning('try to resume battle...')
    kirafan.objects['center'].click_sec(75)
    if kirafan.icons['hai'].click():
        logging.info('resume battle')
        kirafan.wave_id -= 1
    else:
        logging.error('resume battle failed')
        bot.stop()


def _handle_ok_button(bot):
    '''
    1. session clear
    2. disconnect?
    '''
    logging.warning('discover ok button')
    if kirafan.icons['kuromon'].scan(4):
        _battle_resume(bot)
    else:
        logging.warning('maybe network disconnect?')
