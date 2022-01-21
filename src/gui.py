'''
Note:
    set debug level 測試
    log window open/hide (main)
    friend support area (tab)
    adb frame  (main)
    set_timer frame (main)
    wave hide/unhide
    item exchange shop
'''
from log import logging
from typeguard import typechecked
import PySimpleGUI as sg
from thread import Job
from data import uData
from run import run, kirafan
from defined import List, Optional, Dict
import json
import copy
# from adb import adb
from visit_friend_room import run as visit_friend_room


class Tab_Frame():
    def __init__(self, id: str, name: str, quest: Dict):
        self.id = id
        self.quest = quest
        self.name = name
        self.loop_count_status = self.quest['loop_count']
        self.wave_status = 1
        self.__prefix_key = f'_{id}_{name}'
        self.update_original_quest()

    def create_layout(self):
        return [
            self.__info_modify(),
            self.__crea_stop(),
            self.__loop_count(),
            self.__stamina_area(),
            self.__orb_area(),
            self.__wave_area()
        ]

    def __info_modify(self):
        return [
            sg.Input(self.name, key=f'{self.__prefix_key}_title_', size=20),
            sg.Button('Rename', key=f'{self.__prefix_key}_rename_', size=6),
            sg.Button('Delete', key=f'{self.__prefix_key}_delete_', size=6)
        ]

    def __crea_stop(self):
        k = [f'{self.__prefix_key}_crea_stop_']
        return [
            sg.Checkbox('crea_stop', key=k[0], default=self.quest['crea_stop'], enable_events=True)
        ]

    def __loop_count(self):
        k = [f'{self.__prefix_key}_loop_count_status_', f'{self.__prefix_key}_loop_count_setting_']
        return [
            sg.Text(f'loop_count = {self.loop_count_status} of', key=k[0]),
            sg.Input(self.quest['loop_count'], key=k[1], size=(3, 1), pad=0, enable_events=True)
        ]

    def __stamina_area(self):
        stamina = self.quest['stamina']
        k = [f'{self.__prefix_key}_stamina_use_', f'{self.__prefix_key}_stamina_priority_']
        frame_layout = [[
            sg.Checkbox('use', key=k[0], default=stamina['use'], enable_events=True),
            sg.Text('priority:', pad=((5, 0), 5)),
            sg.Input(' > '.join(stamina['priority']), size=20, key=k[1], disabled_readonly_background_color=('white' if stamina['use'] else 'gray'), disabled=True)  # noqa: E501
        ]]
        return [sg.Frame('stamina', frame_layout)]

    def __orb_area(self):
        orb = self.quest['orb']
        k = [f'{self.__prefix_key}_orb_name_']
        frame_layout = [
            [sg.Text('name:'), sg.Input(orb['orb_name'], key=k[0], pad=((2, 0), 5), size=(30, 1), enable_events=True)],
            *[(sg.Text(f'option {n}:'), sg.Checkbox('use', key=f'{self.__prefix_key}_orb{n}_use_', default=orb[n]['use'], enable_events=True),  # noqa: E501
               sg.Text('wave_N:', pad=((5, 2), 5)), sg.InputCombo([i for i in range(1, 6)], key=f'{self.__prefix_key}_orb{n}_wave_N_', default_value=orb[n]['wave_N'], pad=((0, 10), 5), disabled=(not orb[n]['use']), enable_events=True),  # noqa: E501
               sg.Text('myTurn:', pad=((5, 2), 5)), sg.Spin([i for i in range(0, 100)], size=(2, 1), key=f'{self.__prefix_key}_orb{n}_myturn_', initial_value=orb[n]['myturn'], pad=((0, 10), 5), disabled=(not orb[n]['use']), enable_events=True),  # noqa: E501
               sg.Text('target:', pad=((5, 2), 5)), sg.InputCombo(('A', 'B', 'C', 'N'), key=f'{self.__prefix_key}_orb{n}_target_', default_value=orb[n]['target'], pad=((0, 10), 5), disabled=(not orb[n]['use']), enable_events=True)  # noqa: E501
               ) for n in map(str, range(1, 4))]
        ]
        return [sg.Frame('orb', frame_layout)]

    def __wave_area(self):
        w = self.quest['wave']
        k = [f'{self.__prefix_key}_wave_status_', f'{self.__prefix_key}_wave_setting_']
        frame_layout = [[
            sg.Text(f'wave = {self.wave_status} /', key=k[0], pad=((5, 2), 5)),
            sg.InputCombo((1, 2, 3, 5), key=k[1], pad=0, default_value=w['total'], enable_events=True)
        ]]
        for N in map(str, range(1, w['total'] + 1)):
            k = [f'{self.__prefix_key}_wave{N}_auto_', f'{self.__prefix_key}_wave{N}_sp_weight_enable_']
            column = [sg.Text(f'wave{N}:'), sg.Checkbox('auto', key=k[0], default=w[N]['auto'], enable_events=True),
                      sg.Checkbox('sp_weight', key=k[1], default=(w[N]['sp_weight_enable']), enable_events=True),
                      sg.Text('character', pad=((5, 0), 5))]
            for p in ['left', 'middle', 'right']:
                k = [f'{self.__prefix_key}_wave{N}_character_{p}_skill_priority_',
                     f'{self.__prefix_key}_wave{N}_character_{p}_sp_weight_']
                column += [
                  sg.Text(f'{p}:', pad=((5, 2), 5)),
                  sg.Input(' > '.join(w[N][f'character_{p}']['skill_priority']), pad=((0, 0), 5), size=(29), key=k[0], disabled_readonly_background_color=('gray' if w[N]['auto'] else 'white'), disabled=True),  # noqa: E501
                  sg.Text('weight:', pad=((1, 2), 5)),
                  sg.Spin([i for i in range(1, 10)], pad=(((0, 5), 5) if p == 'right' else ((0, 10), 5)), key=k[1], disabled=(w[N]['auto'] or not w[N]['sp_weight_enable']), initial_value=(w[N][f'character_{p}']['sp_weight']), enable_events=True)  # noqa: E501
                ]
            frame_layout = frame_layout + [column]
        return [sg.Frame('wave', frame_layout)]

    def update_all_bind(self, window):
        for N in map(str, range(1, self.quest['wave']['total'] + 1)):
            self.update_waveN_bind(window, N)
        self.update_stamina_bind(window)

    def update_waveN_bind(self, window, N: str):
        for p in ['left', 'middle', 'right']:
            if not self.quest['wave'][N]['auto']:
                window[f'{self.__prefix_key}_wave{N}_character_{p}_skill_priority_'].bind('<Button-1>', '')
            else:
                window[f'{self.__prefix_key}_wave{N}_character_{p}_skill_priority_'].unbind('<Button-1>')

    def update_stamina_bind(self, window):
        if self.quest['stamina']['use']:
            window[f'{self.__prefix_key}_stamina_priority_'].bind('<Button-1>', '')
        else:
            window[f'{self.__prefix_key}_stamina_priority_'].unbind('<Button-1>')

    def handle(self, window, event, values):
        key = event[len(self.__prefix_key):]
        if key == '_loop_count_setting_':
            self.handle_loop_count_event(values[event])
        elif key.startswith('_stamina_'):
            self.handle_stamina_event(window, key, values[event])
        elif key.startswith('_orb'):
            self.handle_orb_event(window, key, values[event])
        elif key.startswith('_wave'):
            self.handle_wave_event(window, key, values[event])

    def handle_stamina_event(self, window, key, value):
        if '_use_' in key:
            self.quest['stamina']['use'] = value
            window[f'{self.__prefix_key}_stamina_priority_'].Widget.config(readonlybackground=('white' if value else 'gray'))
            self.update_stamina_bind(window)
        elif '_stamina_priority_' in key:
            default = ['Au', 'Ag', 'Cu']
            current_list = list(filter(lambda e: e != '', value.split(' > ')))
            available_list = [x for x in default if x not in [c[:2] for c in current_list]]
            current_list = priority_GUI('stamina', key.replace('_', ' ').strip(), current_list, available_list, default).open()
            if current_list is not None:
                self.quest['stamina']['priority'] = current_list
                window[f'{self.__prefix_key}{key}'].Update(' > '.join(current_list))

    def handle_loop_count_event(self, value: str):
        self.quest['loop_count'] = int(value) if value.isdigit() else value

    def handle_orb_event(self, window, key, value):
        n = key[4]
        key = key[6:-1] if n.isdigit() else key[1:-1]
        if key == 'orb_name':
            self.quest['orb'][key] = value
        elif key == 'use':
            for k in [f'{self.__prefix_key}_orb{n}_myturn_',
                      f'{self.__prefix_key}_orb{n}_wave_N_',
                      f'{self.__prefix_key}_orb{n}_target_']:
                window[k].Update(disabled=(not value))
            self.quest['orb'][n][key] = value
        else:
            self.quest['orb'][n][key] = value

    def handle_wave_event(self, window, key, value):
        N = key[5]
        pos = ['left', 'middle', 'right']
        if '_auto_' in key:
            self.quest['wave'][N]['auto'] = value
            self.update_waveN_bind(window, N)
            for k in ([f'{self.__prefix_key}_wave{N}_sp_weight_enable_'] +
                      [f'{self.__prefix_key}_wave{N}_character_{p}_skill_priority_' for p in pos] +
                      [f'{self.__prefix_key}_wave{N}_character_{p}_sp_weight_' for p in pos]):
                if k.endswith('_sp_weight_enable_'):
                    window[k].Update(disabled=value)
                elif k.endswith('_skill_priority_'):
                    window[k].Widget.config(readonlybackground=('gray' if value else 'white'))
                elif window[f'{self.__prefix_key}_wave{N}_sp_weight_enable_'].get():
                    window[k].Update(disabled=value)
        elif '_sp_weight_enable_' in key:
            for k in [f'{self.__prefix_key}_wave{N}_character_{p}_sp_weight_' for p in pos]:
                window[k].Update(disabled=(not value))
        elif '_skill_priority_' in key:
            default = ['sp', 'wpn_sk', 'L_sk', 'R_sk', 'atk']
            current_list = list(filter(lambda e: e != '', value.split(' > ')))
            available_list = [x for x in default if x not in current_list]
            current_list = priority_GUI('skill', key.replace('_', ' ').strip(), current_list, available_list, default).open()
            if current_list is not None:
                self.quest['wave'][N][f'character_{key[17:key.index("_", 17)]}']['skill_priority'] = current_list if current_list != ['Same as Wave1'] else self.quest['wave']['1'][f'character_{key[17:key.index("_", 17)]}']['skill_priority']  # noqa: E501
                window[f'{self.__prefix_key}{key}'].Update(' > '.join(self.quest['wave'][N][f'character_{key[17:key.index("_", 17)]}']['skill_priority']))  # noqa: E501

    def update_wave_id_status(self, window, w_id):
        window[f'{self.__prefix_key}_wave_status_'].Update(f'wave = {w_id} /')

    def update_loop_count_status(self, window, new_status):
        window[f'{self.__prefix_key}_loop_count_status_'].Update(f'loop_count = {new_status} of')

    def rename_title(self, window, exclude: List):
        new_title = window[f'{self.__prefix_key}_title_'].get()
        if new_title in exclude:
            sg.popup(f"'{new_title}' already exists! please use another name", title='Warning')
            return None
        elif new_title == '':
            sg.popup(f"'{new_title}' is empty! please use another name", title='Warning')
            return None
        else:
            window[self.id].update(title=new_title)
            self.name = new_title
            return new_title

    def is_modified(self) -> bool:
        compare = json.dumps(self.quest, sort_keys=True) != json.dumps(self.__original_quest, sort_keys=True)
        return compare

    def update_original_quest(self):
        self.__original_quest = copy.deepcopy(self.quest)

    def reset(self, window):
        self.loop_count_status = self.quest['loop_count']
        self.wave_status = 1
        self.update_wave_id_status(window, self.wave_status)
        self.update_loop_count_status(window, self.loop_count_status)


class kirafanbot_GUI():
    def __init__(self):
        sg.theme('GreenTan')
        self.data = uData.gui_setting()
        self.layout = self.create_layout()
        self.window = sg.Window(f'kirafan-bot  v{uData.setting["version"]}', self.layout, finalize=True)
        self.update_tab_selected(self.find_tab_by_name(self.data['questList']['quest_selector']).id)
        self.update_tabs_bind()
        self.run_job = Job(target=run)
        self.visit_room_job = Job(target=visit_friend_room)

    def open(self):
        while True:
            event, values = self.window.read()
            if event in (sg.WIN_CLOSED, '_button_Exit_'):
                self.__save()
                self.stop_all_safe()
                break
            tab = self.find_tab_by_key(event)
            print(f'tab={"none" if tab is None else tab.name}, event={event}, '
                  f'(value, type)={(values[event], type(values[event])) if event in values else ("none", "none_type")}')
            if tab:
                self.handle_tab_event(tab, event, values)
            elif event.startswith('_button_'):
                self.handle_button_event(event)
            elif event.startswith('_update_'):
                self.handle_update_event(event, values[event])
            elif event == '_tab_group_':
                self.handle_tab_group_event(values[event])
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

    def update_tab_selected(self, tab):
        self.window[tab].select()

    def update_tabs_bind(self):
        for _, tab in self.tabs.items():
            tab.update_all_bind(self.window)

    def check_configure_and_status(self):
        if (self.data['questList']['quest_selector'] != self.tabs[self.window['_tab_group_'].get()].name or
           self.tabs[self.window['_tab_group_'].get()].is_modified()):
            self.data['questList']['quest_selector'] = self.tabs[self.window['_tab_group_'].get()].name
            self.bt_reset_event()
        logging.info(f'kirafan region = {list(kirafan.region)}')
        logging.info(f'kirafan adb use = {uData.setting["adb"]["use"]}')
        logging.info(f'kirafan quest setting = \x1b[41m{kirafan.quest_name}\x1b[0m')

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

    def handle_tab_event(self, tab, event, values):
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

    def handle_button_event(self, key):
        button_event_map = {
            'Start': lambda k: self.bt_start_event(k),
            'Reset': lambda k: self.bt_reset_event(),
            'Stop once': lambda k: self.bt_stop_once_event(),
            'ScreenShot': lambda k: self.bt_screenshot_event(),
            'Visit Room': lambda k: self.bt_visit_room_event(k)
        }
        button_str = key[len('_button_'):-1]
        button_event_map[button_str](key)

    def bt_start_event(self, key):
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
        self.update_stop_once_status()
        self.tabs[self.window['_tab_group_'].get()].reset(self.window)
        logging.info(f'reset quest: {self.tabs[self.window["_tab_group_"].get()].name} finish')
        if self.data['questList']['quest_selector'] == self.tabs[self.window['_tab_group_'].get()].name:
            self.__reload()

    def bt_stop_once_event(self):
        kirafan.stop_once = not kirafan.stop_once
        self.update_stop_once_status()
        logging.info(f'({str(kirafan.stop_once):>5}) kirafan-bot stop after current battle is completed')

    def bt_screenshot_event(self):
        print(self.tabs)
        print()
        # self.tabs[self.window['_tab_group_'].get()].is_modified()
        # print('')
        # adb.set_update_cv2_IM_cache_flag()
        # kirafan.objects_found_all_print()
        # kirafan.icons_found_all_print()
        # print('')

    def bt_visit_room_event(self, key):
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

    def handle_update_event(self, key, value):
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

    def update_button_start_status(self, new_button_status):
        self.change_other_buttons(self.window['_button_Start_'].GetText())
        self.window['_button_Start_'].Update(new_button_status)
        self.window['_running_quest_status_'].Update('' if new_button_status == 'Start' else self.tabs[self.window['_tab_group_'].get()].name)  # noqa: E501

    def change_other_buttons(self, current_button):
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

    def __button_area(self) -> List:
        button_list = ['Start', 'Reset', 'Stop once', 'ScreenShot', 'Visit Room', 'Exit']
        return [
            *[sg.Button(bt, key=f'_button_{bt}_', mouseover_colors=None, size=(10)) for bt in button_list],
            sg.Text('', key='_stop_status_')
        ]

    def stop_all_safe(self):
        self.stop_safe(self.run_job)
        self.stop_safe(self.visit_room_job)

    def stop_safe(self, job):
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
        # adb.reload()
        kirafan.reload()
        logging.info('kirafan-bot reload configure')


@typechecked
class priority_GUI():
    def __init__(self, priority_type: str, text: str, current_list: List, available_list: List, default_list: List):
        self.type = priority_type
        self.current_list = current_list
        self.available_list = available_list
        self.default_list = default_list
        self.stamina = self.__create_stamina_count_dict()
        self.layout = self.create_layout(text)
        self.window = sg.Window('kirafan-bot priority', self.layout, modal=True)

    def __create_stamina_count_dict(self) -> Optional[Dict]:
        r = None
        if self.type == 'stamina':
            r = dict([(x.split(":") + ['1'])[:2] for x in self.current_list] + [(s, 1) for s in self.available_list])
            self.current_list = list(map(lambda x: x[:2], self.current_list))
        return r

    def create_layout(self, text: str) -> List:
        return [
            [sg.Text(text)],
            [sg.Text('current priority', size=25, pad=((40, 5), (5, 0))), sg.Text('available list', pad=((12, 5), (5, 0)))],
            [
                sg.Column([[sg.Button("↑", size=(1, 2), key="_↑_")], [sg.Button("↓", size=(1, 2), key="_↓_")]]),
                sg.Listbox(values=self.current_list, size=(20, 6), pad=((5, 5), (0, 5)), key="_current_list_",
                           default_values=self.current_list[0] if self.current_list else None),
                sg.Column([[sg.Button("→", size=(3, 1), key="_→_")], [sg.Button("←", size=(3, 1), key="_←_")]]),
                sg.Listbox(values=self.available_list, size=(20, 6), pad=((5, 5), (0, 5)), key="_available_list_")
            ],
            self.__stamina_extend(),
            [sg.Submit('Submit', pad=((170, 5), 5)), sg.Cancel('Cancel')] +
            self.__skill_extend_button(text),
        ]

    def __stamina_extend(self) -> List:
        if self.type != 'stamina':
            return []
        layout = [sg.Text('count:')]
        for s in ['Au', 'Ag', 'Cu']:
            _pad = (((0, 5), 5) if s == 'Cu' else ((0, 100), 5))
            layout += [sg.Text(s, pad=((5, 0), 5))]
            layout += [sg.Spin([i for i in range(1, 11)], initial_value=self.stamina[s], size=(2, 1), pad=_pad, key=f'_stamina_count_{s}_', disabled=(s in self.available_list))]  # noqa: E501
        return layout

    def __skill_extend_button(self, text: str) -> List:
        if self.type == 'skill' and text[4] != '1':
            return [sg.Button('Same as Wave1', pad=((33, 0), 0))]
        return []

    def __sumbit(self) -> Optional[List]:
        r = self.window["_current_list_"].get_list_values()
        if self.type == 'stamina':
            return list(map(lambda s: s + f':{self.window[f"_stamina_count_{s}_"].get()}', r))
        elif self.type == 'skill':
            return r

    def open(self) -> Optional[List]:
        _map = {
            '_↑_': lambda: len(self.window['_current_list_'].get_indexes()) > 0 and self.button_up_arrow(),
            '_↓_': lambda: len(self.window['_current_list_'].get_indexes()) > 0 and self.button_down_arrow(),
            '_←_': lambda: len(self.window['_available_list_'].get_indexes()) > 0 and self.button_left_arrow(),
            '_→_': lambda: len(self.window['_current_list_'].get_indexes()) > 0 and self.button_right_arrow(),
            'Submit': self.__sumbit,
            'Same as Wave1': lambda: ['Same as Wave1']
        }
        while True:
            event, _ = self.window.read()
            if event in (sg.WIN_CLOSED, 'Cancel'):
                self.window.close()
                return
            elif event in ('Same as Wave1', 'Submit'):
                self.window.close()
                return _map[event]()
            else:
                _map[event]()

    def button_up_arrow(self):
        i = self.window['_current_list_'].get_indexes()[0]
        self.current_list.insert(i-1 if i else len(self.current_list)+1, self.current_list.pop(i))
        self.window['_current_list_'].Update(self.current_list, set_to_index=(i-1 if i else len(self.current_list)-1))

    def button_down_arrow(self):
        i = self.window['_current_list_'].get_indexes()[0]
        self.current_list.insert(0 if i == len(self.current_list)-1 else i+1, self.current_list.pop(i))
        self.window['_current_list_'].Update(self.current_list, set_to_index=(0 if i == len(self.current_list)-1 else i+1))

    def button_left_arrow(self):
        i = self.window['_available_list_'].get_indexes()[0]
        self.current_list.append(self.available_list.pop(i))
        self.window['_current_list_'].Update(self.current_list)
        self.window['_available_list_'].Update(self.available_list, set_to_index=i if len(self.available_list) > i else i-1)
        self.update_stamina_spin()

    def button_right_arrow(self):
        i = self.window['_current_list_'].get_indexes()[0]
        self.available_list.append(self.current_list.pop(i))
        self.available_list = [x for x in self.default_list if x in self.available_list]
        self.window['_current_list_'].Update(self.current_list, set_to_index=i if len(self.current_list) > i else i-1)
        self.window['_available_list_'].Update(self.available_list)
        self.update_stamina_spin()

    def update_stamina_spin(self):
        if self.type == 'stamina':
            for s in ['Au', 'Ag', 'Cu']:
                self.window[f'_stamina_count_{s}_'].Update(disabled=(s in self.available_list))


uKirafanbotGUI = kirafanbot_GUI()
