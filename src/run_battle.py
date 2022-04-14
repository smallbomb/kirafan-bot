import threading
from log import logger
from typeguard import typechecked
from bot import kirafan


def run(window):
    bot = threading.currentThread()
    bot.trigger_scan_training_button = False
    bot.send_event = lambda event, value: bot.is_not_gui_button_stop() and window.write_event_value(event, value)
    logger.info('battle start...')
    logger.info(f'loop count = {kirafan.loop_count} now')
    while bot.is_running():
        if _is_battle_now():
            if kirafan.wave_change_flag:
                logger.info(f'wave({kirafan.wave_id}/{kirafan.wave_total}) now...')
                bot.send_event('_update_wave_id_', kirafan.wave_id)
                bot.send_event('_update_stop_once_', None)
            if kirafan.ck_timer_pause(lambda: not bot.is_running(), lambda s: bot.send_event('_timer_countdown_', s)):
                continue
            _handle_battle_flows()
        else:
            # is not battle (maybe transitions, loading, sp animation, crash ... etc)
            if kirafan.detect_crashes():
                logger.warning('battle(): detect crashes')
                _battle_resume(bot)
            elif _is_last_wave():
                _handle_award_flows(bot)
            else:
                logger.debug(f'battle(): transitions now...({kirafan.wave_id}/{kirafan.wave_total})')
                kirafan.break_sleep(kirafan.sleep['wave_transitions'], lambda: not bot.is_running())
    logger.info('kirafan-bot stop(battle)...')
    bot.send_event('_update_button_start_', 'Start')
    if bot.trigger_scan_training_button:
        bot.send_event('_button_Scan Training_', None)


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
            logger.debug(f'_handle_battle_flows(): character({wave.ch_id:<6}) action start')
            wave.charater_action()
            logger.debug(f'_handle_battle_flows(): character({wave.ch_id:<6}) action finish')
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
        logger.debug('_handle_award_flows(): try to move next new battle')
        _try_to_move_next_new_battle(bot)
    elif kirafan.icons['ok'].click(adb_update_cache=False):
        _handle_ok_button(bot)
    else:
        logger.debug('_handle_award_flows(): still loading now...')
        kirafan.break_sleep(1, lambda: not bot.is_running())


def _try_to_move_next_new_battle(bot):
    _skip_award_result(bot)
    while bot.is_running():
        if _ck_move_to_next_battle(bot):
            logger.debug('_try_to_move_next_new_battle(): player is moving to next battle...')
            logger.info(f'loop count = {kirafan.loop_count} now')
            kirafan.break_sleep(kirafan.sleep['loading'], lambda: not bot.is_running())
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
            logger.debug('_try_to_move_next_new_battle(): click tojiru button (stamina page was not closed)')
            kirafan.icons['again'].scan_then_click(scan_timeout=3)
        else:
            if kirafan.move_training_place_after_battle:
                kirafan.icons['tojiru'].click(adb_update_cache=False)
                kirafan.break_sleep(1, lambda: not bot.is_running())
                kirafan.icons['tojiru'].scan_then_click(scan_timeout=3)
                kirafan.break_sleep(5, lambda: not bot.is_running())
                bot.stop()
                bot.trigger_scan_training_button = True
            else:
                logger.error('Can not move to next new battle. maybe insufficient stamina items? pause now...')
                bot.send_event('_update_button_start_', 'Start')
                bot.pause()
                bot.wait()


def _skip_award_result(bot):
    logger.debug("_skip_award_result(): handle award result page")
    if kirafan.stop_once:
        logger.debug('kirafan-bot will be stop beacause stop_once be setup.')
        kirafan.stop_once = False
        bot.send_event('_update_stop_once_', None)
        bot.stop()
    elif kirafan.loop_count <= 0 and not kirafan.move_training_place_after_battle:
        logger.info(f'loop count({kirafan.loop_count}) less than or equal to 0')
        bot.stop()

    ct, retry = 12, True
    while bot.is_running():
        kirafan.objects['center_left'].click(ct)
        if not bot.is_running():
            logger.debug('_skip_award_result(): interrupt')
            break
        elif kirafan.icons['again'].found():
            if kirafan.loop_count > 0 or not kirafan.move_training_place_after_battle:
                kirafan.icons['again'].click(adb_update_cache=False)
            break
        elif _ck_tojiru_window_in_award(bot):
            retry = True
            ct = 8
        elif retry:
            logger.debug('_skip_award_result(): try a again because again.png not match on game region')
            retry = False
        else:
            logger.error('_skip_award_result(): again.png not match on game region')
            bot.stop()


@typechecked
def _ck_tojiru_window_in_award(bot) -> bool:
    """
    1. crea comm
    2. nakayoshido
    3. crea craft
    """
    if kirafan.objects['center_left'].found(False):
        # Is nakayoshido or crea craft?
        if kirafan.crea_craft_stop and kirafan.icons['crea_craft_occur'].found(False):
            logger.info('crea stop: crea craft mission')
            bot.stop()
            return True
        if kirafan.icons['tojiru'].click(adb_update_cache=False):
            logger.debug('_ck_tojiru_window_in_award(): nakayoshido or crea craft appears')
            return True
        return False
    elif kirafan.icons['crea_comm_done'].found(False):
        # crea comm
        if kirafan.crea_comm_stop:
            logger.info('crea stop: crea communication done')
            bot.stop()
            return True
        return kirafan.icons['tojiru'].click(adb_update_cache=False)
    return False


@typechecked
def _ck_move_to_next_battle(bot) -> bool:
    def _ck_stamina(bot) -> bool:
        if kirafan.use_stamina(lambda: not bot.is_running()):
            return kirafan.icons['again'].scan_then_click(scan_timeout=3)
        bot.stop()
        return False

    if kirafan.stamina['use'] and kirafan.icons['stamina_title'].scan(2.5):
        return _ck_stamina(bot)
    elif kirafan.icons['kuromon'].scan(kirafan.sleep['loading']):
        return True
    elif kirafan.stamina['use'] and kirafan.icons['stamina_title'].found(False):
        return _ck_stamina(bot)
    return False


def _battle_resume(bot):
    logger.warning('_battle_resume(): try to resume battle...')
    kirafan.reset_crash_detection()
    kirafan.objects['center'].click_sec(100, interrupt=lambda: not bot.is_running())
    if not bot.is_running():
        return
    while kirafan.icons['ok'].click():
        kirafan.break_sleep(2, lambda: not bot.is_running())
    if kirafan.icons['hai'].click():
        logger.info('_battle_resume(): resume battle success')
        kirafan.wave_id -= 1
    else:
        logger.error('_battle_resume(): resume battle failed')
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
