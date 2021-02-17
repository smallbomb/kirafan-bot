import logging
import threading
from typeguard import typechecked
from time import sleep
from bot import BOT


kirafan = BOT()


def run():

    @typechecked
    def _handle_result_page() -> str:
        '''skip 'tojiru' or 'ok' event
        '''
        ct = 12
        while True:
            kirafan.objects['center_left'].click(ct)
            if kirafan.icons['again'].click():
                return 'found again'
            elif kirafan.icons['tojiru'].scan(1):
                logging.debug('icon: tojiru icon found')
                # Indicates that the crea result page to check whether the color of "center_left" is found
                if kirafan.crea_stop and kirafan.objects['center_left'].found():
                    return 'crea interrupt'
                kirafan.icons['tojiru'].click()
                ct -= 2
                continue
            elif kirafan.icons['ok'].click():
                logging.error('icon: ok icon found')
                continue
            else:
                return 'not found again'

    thread = threading.currentThread()
    logging.info('kirafan start...')
    logging.info('loop_count = {} now'.format(kirafan.loop_count))
    while thread.is_running():
        if kirafan.update_waveID():
            if kirafan.wave_change_flag:
                logging.info('wave-{}/{} now...'.format(kirafan.wave_id, kirafan.wave_total))

            wave = kirafan.get_current_wave()
            if wave.auto:
                if not wave.objects['auto_button'].found():
                    wave.objects['auto_button'].click()
            elif wave.is_myTurn():
                if wave.update_characterID():
                    logging.debug('character_%d action start' % wave.ch_id)
                    wave.charater_action()
                    kirafan.objects['center'].moveTo()
                    logging.debug('character_%d action finish' % wave.ch_id)
                else:
                    logging.error('wave-{}/{}: character not found'.format(wave.id, wave.total))
            else:
                kirafan.objects['center'].click_sec(1)
        elif kirafan.wave_id == kirafan.wave_total or kirafan.wave_change_flag is None:  # maybe finish?
            logging.debug("not battle")
            if kirafan.icons['kirara_face'].scan(2):
                logging.debug('kirara_face was found')
                if kirafan.loop_count <= 0:
                    logging.info('loop_count(%d) less than or equal to 0' % kirafan.loop_count)
                    break

                status = _handle_result_page()
                if status == 'crea interrupt':
                    logging.info('crea_stop: crea mission start...?')
                    break
                elif status == 'not found again':
                    logging.error('icon: again.png not found...')
                    break
                elif status == 'found again' and kirafan.stamina['used'] and kirafan.icons['stamina_Au'].scan(2):
                    # again.png is found but player has no stamina.
                    if not kirafan.use_stamina():
                        logging.error('use stamina recovery item failed')
                        break
                    if not kirafan.icons['again'].click():
                        logging.error('icon: again.png not found after use stamina')
                        break

                # check kuromon icon
                if kirafan.icons['kuromon'].scan(2):
                    kirafan.loop_count -= 1
                    logging.info('loop_count = {} now'.format(kirafan.loop_count))
                    sleep(kirafan.sleep['loading'])
                else:
                    logging.error('kuromon not was found... maybe insufficient stamina items? pause now...')
                    thread.pause()

            elif kirafan.session_check and kirafan.icons['ok'].click():
                logging.error('discover ok button')
                kirafan.objects['center'].click_sec(60)
                if kirafan.icons['hai'].click():
                    logging.error('resume battle')
                else:
                    logging.error('resume battle failed')
            else:
                logging.debug('still loading now...')
                sleep(1)
                # error_status += 1
        else:
            logging.debug('transitions now...({}/{})'.format(kirafan.wave_id, kirafan.wave_total))
            sleep(kirafan.sleep['wave_transitions'])
        thread.is_pause()
    logging.info('kirafan stop...')
