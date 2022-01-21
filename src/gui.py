'''
Note:
    set debug level 測試
    log window open/hide (main)
    friend support area (tab)
    set_timer frame (main)
    wave hide/unhide
    item exchange shop
'''
import re
import PySimpleGUI as sg
from log import logging
from data import uData
from typeguard import typechecked
from defined import List, Optional, Dict
from thread import Job
from gui_tab_frame import Tab_Frame
from run import run, kirafan
from visit_friend_room import run as visit_friend_room
from hotkey import Hotkey
from adb import adb


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
        self.run_job = Job(target=run)
        self.visit_room_job = Job(target=visit_friend_room)
        self.hotkey = Hotkey('s', mode='gui', window=self.window)
        if self.data['adb']['use']:
            self.hotkey.remove_all_hotkey()
        self._open_re = re.compile(r'^_(\d+|button|update|tab_group|adb)_.*$')

    def open(self):
        _map = {
            'tab': lambda event, values: self.handle_tab_event(self.find_tab_by_key(event), event, values),
            'tab_group': lambda event, values: self.handle_tab_group_event(values[event]),
            'adb': lambda event, values: self.handle_adb_event(event, values[event]),
            'button': lambda event, values: self.handle_button_event(event),
            'update': lambda event, values: self.handle_update_event(event, values[event])
        }
        while True:
            event, values = self.window.read()
            if event in (sg.WIN_CLOSED, '_button_Exit_'):
                self.__save()
                self.stop_all_safe()
                break

            print(f'event={event}, '
                  f'(value, type)={(values[event], type(values[event])) if event in values else ("none", "none_type")}')
            matchresult = self._open_re.match(event)
            if matchresult:
                _cls = 'tab' if matchresult[1].isdigit() else matchresult[1]
                _map[_cls](event, values)
            else:
                print(f'{event} not match')
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
           self.tabs[self.window['_tab_group_'].get()].is_modified()):
            self.data['questList']['quest_selector'] = self.tabs[self.window['_tab_group_'].get()].name
            self.bt_reset_event()
        logging.info(f'kirafan region = {list(kirafan.region)}')
        logging.info(f'kirafan adb use = {uData.setting["adb"]["use"]}')
        logging.info(f'kirafan quest setting = \x1b[41m{kirafan.quest_name}\x1b[0m')

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
        if tab_id is not None and int(tab_id) == int(self.next_id) - 1:
            tab = self.find_tab_by_name('＋')
            self.data['questList']['＋'] = tab.quest
            new_name = __gen_tab_name()
            self.window[f'_{tab.id}_{tab.name}_title_'].update(new_name)
            self.handle_tab_event(tab, '_rename_', None)
            self.window['_tab_group_'].add_tab(self.__tab_plus()[0])

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
            'ScreenShot': lambda k: self.bt_screenshot_event(),
            'Visit Room': lambda k: self.bt_visit_room_event(k)
        }
        button_str = key[len('_button_'):-1]
        button_event_map[button_str](key)

    def bt_start_event(self, key: str):
        bt_name = self.window[key].GetText()
        if bt_name == 'Start':
            self.check_configure_and_status()
            if not self.run_job.is_alive():
                logging.info('press start now!')
                self.run_job = Job(target=run, args=(self.window,))
                self.run_job.start()
            elif self.run_job.is_pausing():
                logging.info('press resume now!')
                self.run_job.resume()
            self.change_other_buttons(bt_name)
            self.window[key].Update('Stop')
            self.window['_running_quest_status_'].Update(self.tabs[self.window['_tab_group_'].get()].name)
        elif bt_name == 'Stop':
            self.window[key].Update('Start', disabled=True)
            if self.run_job.is_alive():
                self.window['_stop_status_'].Update('Please wait for a while')
                self.window.Refresh()
                self.stop_safe(self.run_job)
                self.window['_stop_status_'].Update('')
            self.change_other_buttons(bt_name)
            self.window[key].Update(disabled=False)
            self.window['_running_quest_status_'].Update('')

    def bt_reset_event(self):
        self.__save()
        if self.data['questList']['quest_selector'] == self.tabs[self.window['_tab_group_'].get()].name:
            self.__reload()
        self.update_stop_once_status()
        self.tabs[self.window['_tab_group_'].get()].reset(self.window)
        logging.info(f'reset quest: {self.tabs[self.window["_tab_group_"].get()].name} finish')

    def bt_stop_once_event(self):
        kirafan.stop_once = not kirafan.stop_once
        self.update_stop_once_status()
        logging.info(f'({str(kirafan.stop_once):>5}) kirafan-bot stop after current battle is completed')

    def bt_screenshot_event(self):
        self.tabs[self.window['_tab_group_'].get()].is_modified()
        # print('')
        # adb.set_update_cv2_IM_cache_flag()
        # kirafan.objects_found_all_print()
        # kirafan.icons_found_all_print()
        # print('')

    def bt_visit_room_event(self, key: str):
        bt_name = self.window[key].GetText()
        if bt_name == 'Visit Room':
            if not self.visit_room_job.is_alive():
                self.visit_room_job = Job(target=visit_friend_room, args=(self.window,))
                self.visit_room_job.start()
            elif self.visit_room_job.is_pausing():
                self.visit_room_job.resume()
            self.change_other_buttons(bt_name)
            self.window[key].Update('Stop Visit')
        elif bt_name == 'Stop Visit':
            self.window[key].Update('Visit Room', disabled=True)
            if self.visit_room_job.is_alive():
                self.window['_stop_status_'].Update('Please wait for a while')
                self.window.Refresh()
                self.stop_safe(self.visit_room_job)
                self.window['_stop_status_'].Update('')
            self.change_other_buttons(bt_name)
            self.window[key].Update(disabled=False)

    def handle_update_event(self, key: str, value):
        update_event_map = {
            '_update_wave_id_': lambda v: self.find_tab_by_name(self.data['questList']['quest_selector']).update_wave_id_status(self.window, v),  # noqa: E501
            '_update_loop_count_': lambda v: self.find_tab_by_name(self.data['questList']['quest_selector']).update_loop_count_status(self.window, v),  # noqa: E501
            '_update_stop_once_': lambda v: self.update_stop_once_status(),
            '_update_button_start_': lambda v: self.update_button_start_status(v),
            '_update_button_friend_start_': lambda v: (self.change_other_buttons(self.window['_button_Visit Room_'].GetText()),
                                                       self.window['_button_Visit Room_'].Update(v))
        }
        update_event_map[key](value)

    def update_stop_once_status(self):
        self.window['_button_Stop once_'].Update('Cancel' if kirafan.stop_once else 'Stop once')

    def update_button_start_status(self, new_button_status: str):
        self.change_other_buttons(self.window['_button_Start_'].GetText())
        self.window['_button_Start_'].Update(new_button_status)
        self.window['_running_quest_status_'].Update('' if new_button_status == 'Start' else self.tabs[self.window['_tab_group_'].get()].name)  # noqa: E501

    def change_other_buttons(self, current_button: str):
        change_other_buttons_map = {
            'Visit Room': lambda: (self.window['_button_Start_'].Update(disabled=True),
                                   self.window['_button_Stop once_'].Update(disabled=True)),
            'Stop Visit': lambda: (self.window['_button_Start_'].Update(disabled=False),
                                   self.window['_button_Stop once_'].Update(disabled=False)),
            'Start': lambda: (self.window['_button_Visit Room_'].Update(disabled=True)),
            'Stop': lambda: (self.window['_button_Visit Room_'].Update(disabled=False)),
        }
        change_other_buttons_map[current_button]()

    def create_layout(self) -> List:
        return [
            self.__run_quest_selector(),
            self.__tab_group_area(),
            self.__adb_area(),
            self.__button_area(),
        ]

    def __run_quest_selector(self) -> List:
        return [sg.Text('Running:', pad=((5, 0), 5)), sg.Text('', font=('Arial', 11, 'bold'), key='_running_quest_status_')]

    def __tab_group_area(self) -> List:
        self.tabs = {str(i): Tab_Frame(str(i), name, self.data['questList'][name])
                     for i, name in enumerate(filter(lambda x: x != 'quest_selector', self.data['questList'].keys()))}
        self.next_id = str(len(self.tabs))
        return [
            [sg.TabGroup([
                [sg.Tab(tab.name, tab.create_layout(), key=id) for id, tab in self.tabs.items()],
                self.__tab_plus()
            ], key='_tab_group_', selected_title_color='red', enable_events=True)]
        ]

    def __tab_plus(self) -> List:
        tab = self.tabs[self.next_id] = Tab_Frame(self.next_id, '＋', uData.create_default_quest())
        self.next_id = str(int(self.next_id) + 1)
        return [sg.Tab(tab.name, tab.create_layout(), key=tab.id)]

    def __adb_area(self) -> List:
        adb = self.data['adb']
        frame_layout = [[
            sg.Checkbox('use', default=adb['use'], key='_adb_use_', enable_events=True),
            sg.Text('serial:', pad=((5, 0), 5)),
            sg.Input(adb['serial'], key='_adb_serial_', size=13, disabled_readonly_background_color=('white' if adb['use'] else 'gray'), disabled=True),  # noqa: E501
            sg.Text('path:', pad=((5, 0), 5)),
            sg.Input(adb['path'], key='_adb_path_', size=30, enable_events=True, disabled_readonly_background_color=('white' if adb['use'] else 'gray'), disabled=True),  # noqa: E501
            sg.FileBrowse(key='_adb_browse_', disabled=not adb['use'])
        ]]
        return [sg.Frame('adb', frame_layout)]

    def __button_area(self) -> List:
        button_list = ['Start', 'Reset', 'Stop once', 'ScreenShot', 'Visit Room', 'Exit']
        return [
            *[sg.Button(bt, key=f'_button_{bt}_', mouseover_colors=None, size=(10)) for bt in button_list],
            sg.Text('', key='_stop_status_')
        ]

    def stop_all_safe(self):
        self.stop_safe(self.run_job)
        self.stop_safe(self.visit_room_job)

    def stop_safe(self, job: Job):
        if job.is_alive():
            job.gui_button_stop()
            job.join()
            job.gui_button_stop_finish()

    def __save(self):
        uData.save_gui_setting()
        if self.window['_tab_group_'].get():  # is None if event == sg.exit
            self.tabs[self.window['_tab_group_'].get()].update_original_quest()

    def __reload(self):
        uData.reload()
        adb.reload()
        kirafan.reload()
        logging.info('kirafan-bot reload configure')
