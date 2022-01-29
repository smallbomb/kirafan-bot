import threading
from log import logger
from typeguard import typechecked
from time import sleep
from bot import kirafan


def run(window):
    bot = threading.currentThread()
    bot.send_event = lambda event, value: bot.is_not_gui_button_stop() and window.write_event_value(event, value)
    logger.info('kirafan start...')
    logger.info(f'loop_count = {kirafan.loop_count} now')
    while bot.is_running():
        if _is_battle_now():
            if kirafan.wave_change_flag:
                logger.info(f'wave({kirafan.wave_id}/{kirafan.wave_total}) now...')
                bot.send_event('_update_wave_id_', kirafan.wave_id)
                bot.send_event('_update_stop_once_', None)
            if kirafan.ck_timer_pause(lambda: not bot.is_running(), lambda s: bot.send_event('_timer_show_', s)):
                continue
            _handle_battle_flows()
        else:
            # is not battle (maybe transitions, loading, sp animation, crash ... etc)
            if kirafan.detect_crashes():
                logger.warning('detect crashes')
                _battle_resume(bot)
            elif _is_last_wave():
                _handle_award_flows(bot)
            else:
                logger.debug(f'transitions now...({kirafan.wave_id}/{kirafan.wave_total})')
                sleep(kirafan.sleep['wave_transitions'])
    logger.info('kirafan stop...')
    bot.send_event('_update_button_start_', 'Start')


@typechecked
def _is_battle_now() -> bool:
    return kirafan.wave_icon_found()


def _handle_battle_flows():
    wave = kirafan.get_current_wave()

    if wave.auto:
        wave.auto_click()
    elif wave.is_myTurn():
        if wave.character_found():
            if wave.friend_action() or wave.orb_action():
                return
            logger.debug(f'character({wave.ch_id:<6}) action start')
            wave.charater_action()
            logger.debug(f'character({wave.ch_id:<6}) action finish')
        else:
            logger.error(f'wave-{wave.id}/{wave.total}: character not found')
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
        bot.send_event('_update_loop_count_', kirafan.loop_count)
        logger.debug('try to move next new battle')
        _try_to_move_next_new_battle(bot)
    elif kirafan.icons['ok'].click(adb_update_cache=False):
        _handle_ok_button(bot)
    else:
        logger.debug('still loading now...')
        sleep(1)


def _try_to_move_next_new_battle(bot):
    _skip_award_result(bot)
    while bot.is_running():
        if _ck_move_to_next_battle(bot):
            logger.debug('player is moving to next battle...')
            logger.info(f'loop_count = {kirafan.loop_count} now')
            sleep(kirafan.sleep['loading'])
            break
        elif not bot.is_running():
            break
        elif kirafan.icons['ok'].click(adb_update_cache=False):
            # if event is session clear, bot will not resume battle. because of batttle finish.
            # if event is poor internet connection, just click it.
            logger.debug('_try_to_move_next_new_battle(): click ok button (poor internet connection)')
        elif kirafan.stamina['use'] and (kirafan.icons['stamina_title'].found(False) and
                                         kirafan.icons['tojiru'].click(adb_update_cache=False)):
            # disconnection after using stamina
            sleep(0.5)
            kirafan.icons['again'].click()
            logger.debug('_try_to_move_next_new_battle(): click tojiru button (stamina page was not closed)')
        else:
            logger.error('Can not move to next new battle. maybe insufficient stamina items? pause now...')
            bot.send_event('_update_button_start_', 'Start')
            bot.pause()
            bot.wait()
            break


def _skip_award_result(bot):
    logger.debug("handle award result page")
    if kirafan.stop_once:
        logger.debug('kirafan-bot.stop_once be setup. (z+o)')
        kirafan.stop_once = False
        bot.send_event('_update_stop_once_', None)
        bot.stop()
    elif kirafan.loop_count <= 0:
        logger.info(f'loop_count({kirafan.loop_count}) less than or equal to 0')
        bot.stop()

    ct, retry = 12, True
    while bot.is_running():
        kirafan.objects['center_left'].click(ct)
        if not bot.is_running():
            logger.debug('_skip_award_result(): interrupt')
            break
        elif kirafan.icons['again'].click():
            break
        elif _ck_tojiru_window_in_award(bot):
            retry = True
            ct = 8
        elif retry:
            logger.debug('try a again because again.png not found')
            retry = False
        else:
            logger.error('icon: again.png not found...')
            bot.stop()


@typechecked
def _ck_tojiru_window_in_award(bot) -> bool:
    """
    1. crea comm
    2. nakayoshido
    3. crea craft
    """
    if kirafan.objects['center_left'].found(False):
        # nakayoshido or crea craft
        if kirafan.crea_craft_stop and kirafan.icons['crea_craft_occur'].found(False):
            logger.info('crea_stop: crea craft mission')
            bot.stop()
            return True
        return kirafan.icons['tojiru'].click(adb_update_cache=False)
    elif kirafan.icons['crea_comm_done'].found(False):
        # crea comm
        if kirafan.crea_comm_stop:
            logger.info('crea_stop: crea communication done')
            bot.stop()
            return True
        return kirafan.icons['tojiru'].click(adb_update_cache=False)
    return False


def _ck_move_to_next_battle(bot) -> bool:
    if kirafan.stamina['use'] and kirafan.icons['stamina_title'].scan(2.5):
        if not kirafan.use_stamina(lambda: not bot.is_running()):
            bot.stop()
            return False
        if not kirafan.icons['again'].click():
            return False

    return kirafan.icons['kuromon'].scan(4.5)


def _battle_resume(bot):
    logger.warning('try to resume battle...')
    kirafan.objects['center'].click_sec(100)
    while kirafan.icons['ok'].click():
        sleep(2)
    if kirafan.icons['hai'].click():
        logger.info('resume battle')
        kirafan.reset_crash_detection()
        kirafan.wave_id -= 1
    else:
        logger.error('resume battle failed')
        bot.stop()


def _handle_ok_button(bot):
    '''
    1. session clear
    2. disconnect?
    '''
    logger.warning('discover ok button')
    if kirafan.icons['kuromon'].scan(4):
        _battle_resume(bot)
    else:
        logger.warning('maybe network disconnect?')
