import re
import PySimpleGUI as sg
from log import logging, logger, loglevel
from copy import deepcopy
from data import uData, data_compare
from typeguard import typechecked
from defined import List, Optional, Dict, Callable
from thread import Job
from gui_tab_frame import Tab_Frame
from window import game_region
from bot import kirafan
from adb import adb
from hotkey import Hotkey
from run_battle import run as battle
from run_visit_friend_room import run as visit_friend_room
from run_cork_shop_exchange import run as cork_shop_exchange
from run_scan_training import run as scan_training


@typechecked
class GUI_Handler(logging.Handler):
    def __init__(self, window: sg.Window, multilinekey: str, winddow_blocked: Callable[[], bool]):
        super().__init__()
        sg.cprint_set_output_destination(window, multilinekey)
        self.formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s', datefmt='%m-%d %H:%M')
        self.window_blocked = winddow_blocked
        self._color_code_re = re.compile(r'(.*?)\x1b\[(\d+)m(.*?)\x1b\[0m(.*)')
        self._color_code_map = {
            '32': 'white on magenta',
            '35': 'white on purple',
            '41': 'white on red'
        }

    def emit(self, record):
        if self.window_blocked():
            return
        log = self.formatter.format(record)
        matchresult = self._color_code_re.match(log)
        if matchresult:
            sg.cprint(matchresult[1], end='')
            sg.cprint(matchresult[3], end='', c=self._color_code_map[matchresult[2]])
            sg.cprint(matchresult[4])
        else:
            sg.cprint(log)


@typechecked
class kirafanbot_GUI():
    def __init__(self):
        sg.theme('GreenTan')
        self.data = uData.gui_setting()
        self.layout = self.create_layout()
        self.window = sg.Window(f'kirafan-bot  v{uData.setting["version"]}', self.layout, finalize=True)
        self.update_tab_selected(self.find_tab_by_name(self.data['questList']['quest_selector']).id)
        self.update_tabs_bind()
        self.update_adb_bind()
        self.battle_job = self.visit_room_job = self.cork_shop_job = self.scan_training_job = Job()
        self.hotkey = Hotkey('s', mode='gui', window=self.window)
        if self.data['adb']['use']:
            self.hotkey.remove_all_hotkey()
        logger.propagate = False
        logger.addHandler(GUI_Handler(self.window, '_log_box_', self.blocked))
        self._open_re = re.compile(r'^_(\d+|button|update|tab_group|adb|timer|log_level|sleep)_.*$')

    def open(self):
        _map = {
            'tab': lambda event, values: self.handle_tab_event(self.find_tab_by_key(event), event, values),
            'tab_group': lambda event, values: self.handle_tab_group_event(values[event]),
            'sleep': lambda event, values: self.handle_sleep_event(event, values[event]),
            'timer': lambda event, values: self.handle_timer_event(event, values[event]),
            'adb': lambda event, values: self.handle_adb_event(event, values[event]),
            'button': lambda event, values: self.handle_button_event(event),
            'log_level': lambda event, values: (self.data.update({'loglevel': values[event]}), logger.setLevel(values[event])),
            'update': lambda event, values: self.handle_update_event(event, values[event])
        }
        while True:
            event, values = self.window.read()
            if event in (sg.WIN_CLOSED, '_button_Exit_'):
                self.__save()
                self.stop_all_safe()
                break

            # print(f'event={event}, '
            #       f'(value, type)={(values[event], type(values[event])) if event in values else ("none", "none_type")}')
            matchresult = self._open_re.match(event)
            if matchresult:
                _cls = 'tab' if matchresult[1].isdigit() else matchresult[1]
                _map[_cls](event, values)
        self.window.close()

    def find_tabskey_by_id(self, id: str) -> Optional[str]:
        for k, v in self.tabs.items():
            if v.id == id:
                return k
        return None

    def find_tab_by_key(self, key: str) -> Optional[Tab_Frame]:
        try:
            id = key[key.index('_')+1:key.index('_', 1)]
            return self.tabs[self.find_tabskey_by_id(id)] if id.isdigit() else None
        except ValueError:
            return None

    def find_tab_by_name(self, name: str) -> Optional[Tab_Frame]:
        for tab in self.tabs.values():
            if tab.name == name:
                return tab
        return None

    def update_tab_selected(self, tab_id: str):
        self.window[tab_id].select()

    def update_tabs_bind(self):
        for _, tab in self.tabs.items():
            tab.update_all_bind(self.window)

    def update_adb_bind(self):
        if self.data['adb']['use']:
            self.window['_adb_serial_'].bind('<Button-1>', '')
        else:
            self.window['_adb_serial_'].unbind('<Button-1>')

    def check_configure_and_status(self):
        if (self.data['questList']['quest_selector'] != self.tabs[self.window['_tab_group_'].get()].name or
           self.tabs[self.window['_tab_group_'].get()].is_modified() or
           not data_compare(self.__original_timer, self.data['set_timer']) or
           not data_compare(self.__original_sleep, self.data['sleep'])):
            self.data['questList']['quest_selector'] = self.tabs[self.window['_tab_group_'].get()].name
            self.bt_reset_event()
        logger.info(f'kirafan-bot: region = {list(kirafan.region)}')
        logger.debug(f'kirafan-bot: adb use = \x1b[35m{uData.setting["adb"]["use"]}\x1b[0m')
        logger.debug(f'kirafan-bot: quest setting = \x1b[41m{kirafan.quest_name}\x1b[0m')

    def handle_tab_event(self, tab: Tab_Frame, event: str, values: Optional[Dict]):
        if event.endswith('_rename_'):
            old_name = tab.name
            exclude = [t.name for _, t in self.tabs.items()] + ['quest_selector']
            # magic: tab key will be modified by window[tab_key].Update() after executing tab.hide()
            #        therefore, window['_tab_group_'].get() will confused.
            o_key = self.window['_tab_group_'].get()
            new_name = tab.rename_title(self.window, exclude)
            n_key = self.window['_tab_group_'].get()
            # update key value, avoid tab key being modified.
            if n_key != o_key:
                self.tabs[n_key] = self.tabs.pop(o_key)
            if new_name:
                self.data['questList'] = {new_name if k == old_name else k: v for k, v in self.data['questList'].items()}
                if self.data['questList']['quest_selector'] == old_name:
                    self.data['questList']['quest_selector'] = new_name
        elif event.endswith('_delete_'):
            return_button = sg.popup_ok_cancel(f"Are you sure you want to delete '{tab.name}' tab?", title='Confirm delete')
            if return_button == 'OK':
                del self.data['questList'][tab.name]
                del self.tabs[self.find_tabskey_by_id(tab.id)]
                self.window['_tab_group_'].Widget.hide(int(tab.id))
                if self.data['questList']['quest_selector'] == tab.name:
                    self.data['questList']['quest_selector'] = self.tabs[self.window['_tab_group_'].get()].name if self.window['_tab_group_'].get() else ''  # noqa: E501
                if self.window['_tab_group_'].get() == self.find_tab_by_name('＋').id:
                    k = self.window['_tab_group_'].get()
                    self.window[k].update(disabled=True)
                    self.window[k].update(disabled=False)
        else:
            tab.handle(self.window, event, values)

    def handle_tab_group_event(self, tab_id: Optional[str]):
        def __gen_tab_name():
            i = 1
            while True:
                n = f'new tab {i}'
                if n not in [t.name for _, t in self.tabs.items()]:
                    return n
                i += 1
        self.window['_tab_group_'].set_focus()
        if tab_id is not None and int(tab_id) == int(self.next_id) - 1:
            tab = self.find_tab_by_name('＋')
            self.data['questList']['＋'] = tab.quest
            new_name = __gen_tab_name()
            self.window[f'_{tab.id}_{tab.name}_title_'].update(new_name)
            self.handle_tab_event(tab, '_rename_', None)
            self.window['_tab_group_'].add_tab(self.__tab_plus()[0])

    def handle_sleep_event(self, key: str, value: str):
        key = key[7:-1]
        if value.replace('.', '', 1).isdigit():
            self.data['sleep'][key] = float(value)
        elif value == '':
            self.data['sleep'][key] = 0

    def handle_timer_event(self, key: str, value):
        if key == '_timer_use_':
            for tk in ['_timer_hour_start_', '_timer_min_start_', '_timer_sec_start_',
                       '_timer_hour_end_', '_timer_min_end_', '_timer_sec_end_']:
                self.window[tk].update(disabled=(not value))
            self.data['set_timer']['use'] = value
        elif key == '_timer_countdown_':
            self.window[key].update(value)
        elif key in ['_timer_hour_start_', '_timer_min_start_', '_timer_sec_start_',
                     '_timer_hour_end_', '_timer_min_end_', '_timer_sec_end_']:
            self.data['set_timer']['pause_range'] = '{}:{}:{}-{}:{}:{}'.format(
                self.window['_timer_hour_start_'].get(),
                self.window['_timer_min_start_'].get(),
                self.window['_timer_sec_start_'].get(),
                self.window['_timer_hour_end_'].get(),
                self.window['_timer_min_end_'].get(),
                self.window['_timer_sec_end_'].get()
            )

    def handle_adb_event(self, key: str, value):
        key = key[5:-1]
        if key == 'use':
            if value:
                self.hotkey.remove_all_hotkey()
            else:
                self.hotkey.add_hotkey()
            self.data['adb'][key] = value
            self.window['_adb_serial_'].Widget.config(readonlybackground=('white' if value else 'gray'))
            self.window['_adb_path_'].Widget.config(readonlybackground=('white' if value else 'gray'))
            self.window['_adb_browse_'].update(disabled=(not value))
            self.window['_button_Game region_'].update(disabled=value)
            self.update_tips_information()
            self.update_adb_bind()
            uData.adb_mode_switch()
            adb.reload()
            kirafan.adb_mode_switch()
        elif key == 'path' and self.data['adb'][key] != value:
            self.data['adb'][key] = value
            self.__reload()
        elif key == 'serial':
            new_serial = sg.popup_get_text('new serial:', title='modify serial', default_text=self.data['adb'][key], size=30)
            if new_serial and self.data['adb'][key] != new_serial:
                self.data['adb'][key] = new_serial
                self.window[f'_adb_{key}_'].update(new_serial)
                self.__reload()

    def handle_button_event(self, key: str):
        button_event_map = {
            'Start': lambda k: self.bt_start_event(k),
            'Reset': lambda k: self.bt_reset_event(),
            'Stop once': lambda k: self.bt_stop_once_event(),
            'Visit Room': lambda k: self.bt_visit_room_event(k),
            'Cork Shop': lambda k: self.bt_cork_shop_event(k),
            'Scan Training': lambda k: self.bt_scan_training_event(k),
            'Game region': lambda k: self.bt_game_region_event(),
            'ScreenShot': lambda k: self.bt_screenshot_event(),
            'Log': lambda k: self.window['_log_area_'].update(visible=(not self.window['_log_area_'].visible)),
            'More settings': lambda k: self.window['_more_settings_area_'].update(visible=(not self.window['_more_settings_area_'].visible)),  # noqa: E501
        }
        button_str = key[len('_button_'):-1]
        button_event_map[button_str](key)

    def bt_start_event(self, key: str):
        bt_name = self.window[key].GetText()
        if bt_name == 'Start':
            self.check_configure_and_status()
            if not self.battle_job.is_alive():
                self.battle_job = Job(target=battle, args=(self.window,))
                self.battle_job.start()
            elif self.battle_job.is_pausing():
                self.battle_job.resume()
            self.update_button_status(key, 'Stop')
        elif bt_name == 'Stop':
            if self.battle_job.is_alive():
                self.update_button_status(key, bt_name)
                self.stop_safe(self.battle_job)
            self.update_button_status(key, 'Start')

    def bt_reset_event(self):
        self.__save()
        if self.data['questList']['quest_selector'] == self.tabs[self.window['_tab_group_'].get()].name:
            self.__reload()
        self.update_stop_once_status()
        self.tabs[self.window['_tab_group_'].get()].reset(self.window)
        logger.info(f'kirafan-bot: reset {self.tabs[self.window["_tab_group_"].get()].name} quest finish')

    def bt_stop_once_event(self):
        kirafan.stop_once = not kirafan.stop_once
        self.update_stop_once_status()
        logger.info(f'({str(kirafan.stop_once):>5}) kirafan-bot stop after current battle is completed')

    def bt_screenshot_event(self):
        kirafan.screenshot()

    def bt_game_region_event(self):
        new = list(game_region())
        if self.data['location'] != new:
            self.data['location'] = new
            self.__reload()

    def bt_visit_room_event(self, key: str):
        bt_name = self.window[key].GetText()
        if bt_name == 'Visit Room':
            if not self.visit_room_job.is_alive():
                self.visit_room_job = Job(target=visit_friend_room, args=(self.window,))
                self.visit_room_job.start()
            elif self.visit_room_job.is_pausing():
                self.visit_room_job.resume()
            self.update_button_status(key, 'Stop Visit')
        elif bt_name == 'Stop Visit':
            if self.visit_room_job.is_alive():
                self.update_button_status(key, bt_name)
                self.stop_safe(self.visit_room_job)
            self.update_button_status(key, 'Visit Room')

    def bt_cork_shop_event(self, key: str):
        bt_name = self.window[key].GetText()
        if bt_name == 'Cork Shop':
            if not self.cork_shop_job.is_alive():
                self.cork_shop_job = Job(target=cork_shop_exchange, args=(self.window,))
                self.cork_shop_job.start()
            elif self.cork_shop_job.is_pausing():
                self.cork_shop_job.resume()
            self.update_button_status(key, 'Stop Exchange')
        elif bt_name == 'Stop Exchange':
            if self.cork_shop_job.is_alive():
                self.update_button_status(key, bt_name)
                self.stop_safe(self.cork_shop_job)
            self.update_button_status(key, 'Cork Shop')

    def bt_scan_training_event(self, key: str):
        bt_name = self.window[key].GetText()
        if bt_name == 'Scan Training':
            if not self.scan_training_job.is_alive():
                self.scan_training_job = Job(target=scan_training, args=(self.window,))
                self.scan_training_job.start()
            elif self.scan_training_job.is_pausing():
                self.scan_training_job.resume()
            self.update_button_status(key, 'Stop Scan')
        elif bt_name == 'Stop Scan':
            if self.scan_training_job.is_alive():
                self.update_button_status(key, bt_name)
                self.stop_safe(self.scan_training_job)
            self.update_button_status(key, 'Scan Training')

    def handle_update_event(self, key: str, value):
        update_event_map = {
            '_update_wave_id_': lambda v: self.find_tab_by_name(self.data['questList']['quest_selector']).update_wave_id_status(self.window, v),  # noqa: E501
            '_update_loop_count_': lambda v: self.find_tab_by_name(self.data['questList']['quest_selector']).update_loop_count_status(self.window, v),  # noqa: E501
            '_update_stop_once_': lambda v: self.update_stop_once_status(),
            '_update_button_start_': lambda v: self.update_button_status('_button_Start_', v),
            '_update_button_visit_room_': lambda v: self.update_button_status('_button_Visit Room_', v),
            '_update_button_cork_shop_': lambda v: self.update_button_status('_button_Cork Shop_', v),
            '_update_button_scan_training_': lambda v: self.update_button_status('_button_Scan Training_', v)
        }
        update_event_map[key](value)

    def update_stop_once_status(self):
        self.window['_button_Stop once_'].Update('Cancel' if kirafan.stop_once else 'Stop once')

    def update_button_status(self, key: str, new_button: str):
        old_button = self.window[key].GetText()
        if old_button == new_button:
            self.window[key].Update(disabled=True)
            self.window['_tips_'].Update('Tips: Please wait for a while')
            self.window.Refresh()
            return

        self.window[key].Update(new_button, disabled=False)
        self.toggle_other_buttons(old_button)
        if key == '_button_Start_':
            self.window['_running_status_'].Update('' if new_button == 'Start' else self.tabs[self.window['_tab_group_'].get()].name)  # noqa: E501
        self.update_tips_information()

    def update_tips_information(self):
        if self.blocked():
            return
        if not self.data['adb']['use'] and (self.battle_job.is_alive() or self.visit_room_job.is_alive() or
                                            self.cork_shop_job.is_alive() or self.scan_training_job.is_alive()):
            self.window['_tips_'].update('Tips: press hotkey(z+s) to stop bot')
        else:
            self.window['_tips_'].update('')
            self.window['_timer_countdown_'].update('')

    def toggle_other_buttons(self, current_button: str):
        toggle_other_buttons_map = {
            'Start': lambda: (self.window['_button_Visit Room_'].Update(disabled=True),
                              self.window['_button_Cork Shop_'].Update(disabled=True),
                              self.window['_button_Scan Training_'].Update(disabled=True),
                              self.window['_button_Game region_'].Update(disabled=True)),
            'Visit Room': lambda: (self.window['_button_Start_'].Update(disabled=True),
                                   self.window['_button_Stop once_'].Update(disabled=True),
                                   self.window['_button_Cork Shop_'].Update(disabled=True),
                                   self.window['_button_Scan Training_'].Update(disabled=True),
                                   self.window['_button_Game region_'].Update(disabled=True)),
            'Cork Shop': lambda: (self.window['_button_Start_'].Update(disabled=True),
                                  self.window['_button_Stop once_'].Update(disabled=True),
                                  self.window['_button_Visit Room_'].Update(disabled=True),
                                  self.window['_button_Scan Training_'].Update(disabled=True),
                                  self.window['_button_Game region_'].Update(disabled=True)),
            'Scan Training': lambda: (self.window['_button_Start_'].Update(disabled=True),
                                      self.window['_button_Stop once_'].Update(disabled=True),
                                      self.window['_button_Visit Room_'].Update(disabled=True),
                                      self.window['_button_Cork Shop_'].Update(disabled=True),
                                      self.window['_button_Game region_'].Update(disabled=True)),
            'Stop': lambda: (self.window['_button_Visit Room_'].Update(disabled=False),
                             self.window['_button_Cork Shop_'].Update(disabled=False),
                             self.window['_button_Scan Training_'].Update(disabled=False),
                             self.data['adb']['use'] or self.window['_button_Game region_'].Update(disabled=False)),
            'Stop Visit': lambda: (self.window['_button_Start_'].Update(disabled=False),
                                   self.window['_button_Stop once_'].Update(disabled=False),
                                   self.window['_button_Cork Shop_'].Update(disabled=False),
                                   self.window['_button_Scan Training_'].Update(disabled=False),
                                   self.data['adb']['use'] or self.window['_button_Game region_'].Update(disabled=False)),
            'Stop Exchange': lambda: (self.window['_button_Start_'].Update(disabled=False),
                                      self.window['_button_Stop once_'].Update(disabled=False),
                                      self.window['_button_Visit Room_'].Update(disabled=False),
                                      self.window['_button_Scan Training_'].Update(disabled=False),
                                      self.data['adb']['use'] or self.window['_button_Game region_'].Update(disabled=False)),
            'Stop Scan': lambda: (self.window['_button_Start_'].Update(disabled=False),
                                  self.window['_button_Stop once_'].Update(disabled=False),
                                  self.window['_button_Visit Room_'].Update(disabled=False),
                                  self.window['_button_Cork Shop_'].Update(disabled=False),
                                  self.data['adb']['use'] or self.window['_button_Game region_'].Update(disabled=False)),
        }
        toggle_other_buttons_map[current_button]()

    def create_layout(self) -> List:
        return [
            self.__tab_group_area(),
            self.__more_settings_area(),
            self.__information_area(),
            self.__button_area(),
            self.__log_level_area()
        ]

    def __tab_group_area(self) -> List:
        self.tabs = {str(i): Tab_Frame(str(i), name, self.data['questList'][name])
                     for i, name in enumerate(filter(lambda x: x != 'quest_selector', self.data['questList'].keys()))}
        self.next_id = str(len(self.tabs))
        return [
            [sg.TabGroup([
                [sg.Tab(tab.name, tab.create_layout(), key=id) for id, tab in self.tabs.items()],
                self.__tab_plus()
            ], key='_tab_group_', selected_title_color='red2', focus_color='Any', enable_events=True)]
        ]

    def __tab_plus(self) -> List:
        tab = self.tabs[self.next_id] = Tab_Frame(self.next_id, '＋', uData.create_default_quest())
        self.next_id = str(int(self.next_id) + 1)
        return [sg.Tab(tab.name, tab.create_layout(), key=tab.id)]

    def __more_settings_area(self) -> List:
        return [sg.pin(
            sg.Column([
                self.__sleep_area() + self.__set_timer_area(),
                self.__adb_area()
            ], k='_more_settings_area_', visible=False)
        )]

    def __sleep_area(self) -> List:
        self.__original_sleep = deepcopy(self.data['sleep'])
        delay = self.data['sleep']
        k = ['_sleep_click_', '_sleep_sp_', '_sleep_loadding_', '_sleep_wave_transitions_']
        layout = [[
            sg.Text('click:', pad=((5, 0), 5)),
            sg.Input(delay['click'], size=3, pad=((0, 10), 5), key=k[0], enable_events=True),
            sg.Text('sp:', pad=((5, 0), 5)),
            sg.Input(delay['sp'], size=4, pad=((0, 10), 5), key=k[1], enable_events=True),
            sg.Text('loading:', pad=((5, 0), 5)),
            sg.Input(delay['loading'], size=4, pad=((0, 10), 5), key=k[2], enable_events=True),
            sg.Text('wave transition:', pad=((5, 0), 5)),
            sg.Input(delay['wave_transitions'], size=3, pad=((0, 10), 5), key=k[3], enable_events=True)
        ]]
        return [sg.Frame('delay (s)', layout, pad=((0, 5), 5))]

    def __set_timer_area(self) -> List:
        self.__original_timer = deepcopy(self.data['set_timer'])
        timer = self.data['set_timer']
        k = ['_timer_use_', '_timer_hour_start_', '_timer_min_start_', '_timer_sec_start_',
             '_timer_hour_end_', '_timer_min_end_', '_timer_sec_end_']
        frame_layout = [[
            sg.Checkbox('use', default=timer['use'], key=k[0], enable_events=True),
            sg.Text('pause range(h:m:s):', pad=((5, 0), 5)),
            sg.Spin([f'{("0" + str(i))[-2:]}' for i in range(0, 24)], size=2, key=k[1], readonly=True, initial_value=timer['pause_range'][:2], disabled=(not timer['use']), enable_events=True), sg.Text(':', pad=(0, 0)),  # noqa: E501
            sg.Spin([f'{("0" + str(i))[-2:]}' for i in range(0, 60)], size=2, key=k[2], readonly=True, initial_value=timer['pause_range'][3:5], disabled=(not timer['use']), enable_events=True), sg.Text(':', pad=(0, 0)),  # noqa: E501
            sg.Spin([f'{("0" + str(i))[-2:]}' for i in range(0, 60)], size=2, key=k[3], readonly=True, initial_value=timer['pause_range'][6:8], disabled=(not timer['use']), enable_events=True), sg.Text('  -  ', pad=(0, 0)),  # noqa: E501
            sg.Spin([f'{("0" + str(i))[-2:]}' for i in range(0, 24)], size=2, key=k[4], readonly=True, initial_value=timer['pause_range'][9:11], disabled=(not timer['use']), enable_events=True), sg.Text(':', pad=(0, 0)),  # noqa: E501
            sg.Spin([f'{("0" + str(i))[-2:]}' for i in range(0, 60)], size=2, key=k[5], readonly=True, initial_value=timer['pause_range'][12:14], disabled=(not timer['use']), enable_events=True), sg.Text(':', pad=(0, 0)),  # noqa: E501
            sg.Spin([f'{("0" + str(i))[-2:]}' for i in range(0, 60)], size=2, key=k[6], readonly=True, initial_value=timer['pause_range'][15:17], disabled=(not timer['use']), enable_events=True)  # noqa: E501
        ]]
        return [sg.Frame('timer', frame_layout)]

    def __adb_area(self) -> List:
        adb = self.data['adb']
        frame_layout = [[
            sg.Checkbox('use', default=adb['use'], key='_adb_use_', enable_events=True),
            sg.Text('serial:', pad=((5, 0), 5)),
            sg.Input(adb['serial'], key='_adb_serial_', size=13, disabled_readonly_background_color=('white' if adb['use'] else 'gray'), disabled=True),  # noqa: E501
            sg.Text('path:', pad=((5, 0), 5)),
            sg.Input(adb['path'], key='_adb_path_', size=63, enable_events=True, disabled_readonly_background_color=('white' if adb['use'] else 'gray'), disabled=True),  # noqa: E501
            sg.FileBrowse(key='_adb_browse_', size=7, disabled=not adb['use'])
        ]]
        return [sg.Frame('adb.exe', frame_layout, pad=((0, 5), 5))]

    def __information_area(self) -> List:
        return [
            sg.Text('Running:', pad=((5, 0), 5)), sg.Text('', font=('Any', 11, 'bold'), size=40, key='_running_status_'),
            sg.Column([[sg.Text('', size=30, key='_timer_countdown_')]], expand_x=True, element_justification='center'),
            sg.Column([[sg.Text('', size=30, text_color='red2', justification='right', font=('Any', 11, 'bold'), key='_tips_')
                        ]], expand_x=True, element_justification='right')
        ]

    def __button_area(self) -> List:
        button_list = ['Start', 'Reset', 'Stop once', 'Visit Room', 'Cork Shop', 'Scan Training',
                       'Game region', 'ScreenShot', 'Log', 'More settings', 'Exit']
        return [
            sg.Column([[
                sg.Button(bt, key=f'_button_{bt}_', mouseover_colors=None, size=12, focus=True if bt == 'Reset' else None,
                          disabled=True if bt == 'Game region' and self.data['adb']['use'] else False) for bt in button_list
            ]], element_justification='right', expand_x=True)
        ]

    def __log_level_area(self) -> List:
        level = [
            sg.Column([[
                sg.Text('Log level:', pad=(0, 0)),
                sg.InputCombo([e.name for e in loglevel], default_value=self.data['loglevel'].upper(),
                              key='_log_level_', enable_events=True)
            ]], vertical_alignment='top')
        ]
        box = [sg.Multiline(size=(None, 10), key='_log_box_', pad=(0, 0), expand_x=True)]
        return [sg.pin(sg.Column([box + level], expand_x=True, k='_log_area_', visible=False), expand_x=True)]

    def stop_all_safe(self):
        self.stop_safe(self.battle_job)
        self.stop_safe(self.visit_room_job)
        self.stop_safe(self.cork_shop_job)
        self.stop_safe(self.scan_training_job)

    def stop_safe(self, job: Job):
        if job.is_alive():
            job.gui_button_stop()
            job.join()
            job.gui_button_stop_finish()

    def blocked(self):
        if not (self.battle_job.is_not_gui_button_stop() and self.visit_room_job.is_not_gui_button_stop() and
                self.cork_shop_job.is_not_gui_button_stop() and self.scan_training_job.is_not_gui_button_stop()):
            return True
        return False

    def __save(self):
        uData.save_gui_setting()
        self.__original_sleep = deepcopy(self.data['sleep'])
        self.__original_timer = deepcopy(self.data['set_timer'])
        if self.window['_tab_group_'].get():  # is None if event == sg.exit
            self.tabs[self.window['_tab_group_'].get()].update_original_quest()

    def __reload(self):
        uData.reload()
        adb.reload()
        kirafan.reload()
        logger.info('kirafan-bot: reload configuration finish')
