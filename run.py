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
                logging.info('wave-{}/{} now...'.format(kirafan.wave_id, kirafan.wave_total))
            _handle_battle_flows()
        else:
            # is not battle (maybe transitions, loading, sp animation ... etc)
            if _is_last_wave():
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
        if not wave.objects['auto_button'].found():
            wave.objects['auto_button'].click()
    elif wave.is_myTurn():
        if wave.update_characterID():
            logging.debug('character_%d action start' % wave.ch_id)
            wave.charater_action()
            logging.debug('character_%d action finish' % wave.ch_id)
        else:
            logging.error('wave-{}/{}: character not found'.format(wave.id, wave.total))
    else:
        kirafan.objects['center'].click_sec(1)


@typechecked
def _is_last_wave() -> bool:
    return kirafan.wave_id == kirafan.wave_total or kirafan.wave_change_flag is None


def _handle_award_flows(bot):
    '''
    1. kiraraface?
    2. session clear?
    3. loading?
    '''
    if kirafan.icons['kirara_face'].scan(2):
        logging.debug("try to move next new battle")
        _try_to_move_next_new_battle(bot)
    elif kirafan.icons['ok'].click():
        logging.warning('discover ok button')
        kirafan.objects['center'].click_sec(60)
        if kirafan.icons['hai'].click():
            logging.info('resume battle')
        else:
            logging.error('resume battle failed')
            bot.stop()
    else:
        logging.debug('still loading now...')
        sleep(1)


def _try_to_move_next_new_battle(bot):
    _skip_award_result(bot)
    if bot.is_running():
        if _ck_move_to_next_battle(bot):
            kirafan.loop_count -= 1
            logging.debug('player is moving to next battle...')
            logging.info('loop_count = {} now'.format(kirafan.loop_count))
            sleep(kirafan.sleep['loading'])
        else:
            logging.error('Can not move to next new battle. maybe insufficient stamina items? pause now...')
            bot.pause()
            bot.wait()


def _skip_award_result(bot):
    '''
    Note: the 'tojiru button' or 'ok button' may appear on sreen.
    1. tojiru button -> chara/crea mission
    2. ok button -> maybe network disconnect.
    '''
    logging.debug("handle award result page")
    if kirafan.stop_once:
        logging.debug('kirafan-bot.stop_once be setup. (z+o)')
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
        elif kirafan.icons['ok'].click():
            logging.warning('icon: ok icon found. maybe network disconnect?')
        else:
            logging.error('icon: again.png not found...')
            bot.stop()


def _ck_move_to_next_battle(bot) -> bool:
    # check stamina_Au first. wait for loading time even if user has enough stamina.
    if kirafan.stamina['used'] and kirafan.icons['stamina_Au'].scan(1):
        kirafan.use_stamina()
        kirafan.icons['again'].click()

    return kirafan.icons['kuromon'].scan(3)
