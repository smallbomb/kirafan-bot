import re
import json
import PySimpleGUI as sg
from data import uData
from copy import deepcopy
from typeguard import typechecked
from defined import List, Optional, Dict
from gui_priority import priority_GUI
_tab_handle_re = re.compile(r'^_(loop_count_setting|crea_(?:craft|comm)_stop|friend_support|stamina|orb|wave).*_$')
_tab_handle_wave_event_re = re.compile(r'^_wave\d*_.*(auto|sp_weight_enable|sp_weight|skill_priority|total)_$')
pos = ['left', 'middle', 'right']
sk_list = ['sp', 'wpn_sk', 'L_sk', 'R_sk', 'atk']
stamina_list = ['Au', 'Ag', 'Cu']


@typechecked
class Tab_Frame():
    def __init__(self, id: str, name: str, quest: Dict):
        self.id = id
        self.quest = quest
        self.name = name
        self.loop_count_status = self.quest['loop_count']
        self.wave_status = 1
        self.__prefix_key = f'_{id}_{name}'
        self.update_original_quest()

    def create_layout(self) -> List:
        return [
            self.__loop_count() +
            self.__tab_modify(),
            self.__orb_area() +
            [sg.Column([self.__crea_stop(), self.__stamina_area(), self.__friend_support_area()])],
            self.__wave_area()
        ]

    def __loop_count(self) -> List:
        k = [f'{self.__prefix_key}_loop_count_status_', f'{self.__prefix_key}_loop_count_setting_']
        return [
            sg.Text(f'loop_count = {self.loop_count_status} of', key=k[0]),
            sg.Input(self.quest['loop_count'], key=k[1], size=(3, 1), pad=0, enable_events=True)
        ]

    def __tab_modify(self) -> List:
        return [
            sg.Column([[
                sg.Input(self.name, key=f'{self.__prefix_key}_title_', size=20),
                sg.Button('Rename', key=f'{self.__prefix_key}_rename_', size=7, mouseover_colors=None),
                sg.Button('Delete', key=f'{self.__prefix_key}_delete_', size=7, mouseover_colors=None)
            ]], pad=(0, 0), element_justification='r', expand_x=True)
        ]

    def __orb_area(self) -> List:
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

    def __crea_stop(self) -> List:
        k = [f'{self.__prefix_key}_crea_craft_stop_', f'{self.__prefix_key}_crea_comm_stop_']
        return [
            sg.Checkbox('crea craft stop', key=k[0], pad=((12, 0), 0), default=self.quest['crea_stop']['craft'], enable_events=True),  # noqa: E501
            sg.Checkbox('crea comm stop', key=k[1], default=self.quest['crea_stop']['comm'], enable_events=True)
        ]

    def __stamina_area(self) -> List:
        stamina = self.quest['stamina']
        k = [f'{self.__prefix_key}_stamina_use_', f'{self.__prefix_key}_stamina_priority_']
        frame_layout = [[
            sg.Checkbox('use', key=k[0], default=stamina['use'], enable_events=True),
            sg.Text('priority:', pad=((5, 0), 5)),
            sg.Input(' > '.join(stamina['priority']), size=20, key=k[1], disabled_readonly_background_color=('white' if stamina['use'] else 'gray'), disabled=True)  # noqa: E501
        ]]
        return [sg.Frame('stamina', frame_layout)]

    def __friend_support_area(self) -> List:
        friend_support = self.quest['friend_support']
        k = [f'{self.__prefix_key}_friend_support_use_', f'{self.__prefix_key}_friend_support_wave_N_',
             f'{self.__prefix_key}_friend_support_myturn_', f'{self.__prefix_key}_friend_support_replace_']
        frame_layout = [[
            sg.Checkbox('use', key=k[0], default=friend_support['use'], enable_events=True),
            sg.Text('wave_N:', pad=((5, 2), 5)), sg.InputCombo([i for i in range(1, 6)], key=k[1], default_value=friend_support['wave_N'], disabled=(not friend_support['use']), enable_events=True),  # noqa: E501
            sg.Text('mytuen:', pad=((5, 2), 5)), sg.Spin([i for i in range(0, 100)], size=(2, 1), key=k[2], initial_value=friend_support['myturn'], disabled=(not friend_support['use']), enable_events=True),  # noqa: E501
            sg.Text('replace:', pad=((5, 2), 5)), sg.InputCombo([f'character_{p}' for p in pos], size=15, key=k[3], default_value=friend_support['replace'], disabled=(not friend_support['use']), enable_events=True),  # noqa: E501
        ]]
        return [sg.Frame('friend_support', frame_layout)]

    def __wave_area(self) -> List:
        w = self.quest['wave']
        k = [f'{self.__prefix_key}_wave_status_', f'{self.__prefix_key}_wave_total_']
        frame_layout = [[
            sg.Text(f'wave = {self.wave_status} /', key=k[0], pad=((5, 2), 5)),
            sg.InputCombo((1, 2, 3, 5), key=k[1], pad=0, default_value=w['total'], enable_events=True)
        ]]
        for N in map(str, range(1, w['total'] + 1)):
            frame_layout += self.__a_wave_row(w, N)
        return [sg.Frame('wave', frame_layout, key=f'{self.__prefix_key}_wave_frame_')]

    def __a_wave_row(self, w: Dict, N: str) -> List[List]:
        k = [f'{self.__prefix_key}_wave{N}_auto_', f'{self.__prefix_key}_wave{N}_sp_weight_enable_']
        column = [sg.Text(f'wave{N}:'), sg.Checkbox('auto', key=k[0], default=w[N]['auto'], enable_events=True),
                  sg.Checkbox('sp_weight', key=k[1], default=(w[N]['sp_weight_enable']), disabled=(w[N]['auto']), enable_events=True),  # noqa: E501
                  sg.Text('character', pad=((5, 0), 5))]
        for p in pos:
            k = [f'{self.__prefix_key}_wave{N}_character_{p}_skill_priority_',
                 f'{self.__prefix_key}_wave{N}_character_{p}_sp_weight_']
            column += [
                sg.Text(f'{p}:', pad=((5, 2), 5)),
                sg.Input(' > '.join(w[N][f'character_{p}']['skill_priority']), pad=((0, 0), 5), size=(29), key=k[0], disabled_readonly_background_color=('gray' if w[N]['auto'] else 'white'), disabled=True),  # noqa: E501
                sg.Text('weight:', pad=((1, 2), 5)),
                sg.Spin([i for i in range(1, 10)], pad=(((0, 5), 5) if p == 'right' else ((0, 10), 5)), key=k[1], disabled=(w[N]['auto'] or not w[N]['sp_weight_enable']), initial_value=(w[N][f'character_{p}']['sp_weight']), enable_events=True)  # noqa: E501
            ]
        return [column]

    def update_all_bind(self, window: sg.Window):
        for N in map(str, range(1, self.quest['wave']['total'] + 1)):
            self.update_waveN_bind(window, N)
        self.update_stamina_bind(window)

    def update_waveN_bind(self, window: sg.Window, N: str):
        for p in pos:
            if not self.quest['wave'][N]['auto']:
                window[f'{self.__prefix_key}_wave{N}_character_{p}_skill_priority_'].bind('<Button-1>', '')
            else:
                window[f'{self.__prefix_key}_wave{N}_character_{p}_skill_priority_'].unbind('<Button-1>')

    def update_stamina_bind(self, window: sg.Window):
        if self.quest['stamina']['use']:
            window[f'{self.__prefix_key}_stamina_priority_'].bind('<Button-1>', '')
        else:
            window[f'{self.__prefix_key}_stamina_priority_'].unbind('<Button-1>')

    def handle(self, window: sg.Window, event: str, values: Dict):
        _handle_map = {
            'loop_count_setting': lambda window, key, value: self.handle_loop_count_event(value),
            'orb': lambda window, key, value: self.handle_orb_event(window, key, value),
            'crea_craft_stop': lambda window, key, value: self.quest['crea_stop'].update({'craft': value}),
            'crea_comm_stop': lambda window, key, value: self.quest['crea_stop'].update({'comm': value}),
            'stamina': lambda window, key, value: self.handle_stamina_event(window, key, value),
            'friend_support': lambda window, key, value: self.handle_friend_support_event(window, key, value),
            'wave': lambda window, key, value: self.handle_wave_event(window, key, value)
        }
        key = event[len(self.__prefix_key):]
        matchresult = _tab_handle_re.match(key)
        if matchresult:
            _handle_map[matchresult[1]](window, key, values[event])

    def handle_loop_count_event(self, value: str):
        if value.isdigit():
            self.quest['loop_count'] = int(value)
        elif value == '':
            self.quest['loop_count'] = 0

    def handle_orb_event(self, window: sg.Window, key: str, value):
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

    def handle_stamina_event(self, window: sg.Window, key: str, value):
        if '_use_' in key:
            self.quest['stamina']['use'] = value
            window[f'{self.__prefix_key}_stamina_priority_'].Widget.config(readonlybackground=('white' if value else 'gray'))
            self.update_stamina_bind(window)
        elif '_stamina_priority_' in key:
            current_list = list(filter(lambda e: e != '', value.split(' > ')))
            available_list = [s for s in stamina_list if s not in [c[:2] for c in current_list]]
            current_list = priority_GUI('stamina', key.replace('_', ' ').strip(), current_list, available_list, stamina_list,
                                        window.mouse_location()).open()
            if current_list is not None:
                self.quest['stamina']['priority'] = current_list
                window[f'{self.__prefix_key}{key}'].Update(' > '.join(current_list))

    def handle_friend_support_event(self, window: sg.Window, key: str, value):
        k = key[16:-1]
        self.quest['friend_support'][k] = value
        if k == 'use':
            window[f'{self.__prefix_key}_friend_support_wave_N_'].Update(disabled=(not value))
            window[f'{self.__prefix_key}_friend_support_myturn_'].Update(disabled=(not value))
            window[f'{self.__prefix_key}_friend_support_replace_'].Update(disabled=(not value))

    def handle_wave_event(self, window, key, value):
        _handle_wave_event_map = {
            'auto': lambda w, k, v: self.w_auto_event(w, k, v),
            'sp_weight_enable': lambda w, k, v: self.w_sp_weight_enable_event(w, k, v),
            'sp_weight': lambda w, k, v: self.w_sp_weight_event(k, v),
            'skill_priority': lambda w, k, v: self.w_skill_priority_event(w, k, v),
            'total': lambda w, k, v: self.w_total_event(w, v)
        }
        matchresult = _tab_handle_wave_event_re.match(key)
        if matchresult:
            _handle_wave_event_map[matchresult[1]](window, key, value)

    def w_auto_event(self, window: sg.Window, key: str, value: bool):
        N = key[5]
        self.quest['wave'][N]['auto'] = value
        self.update_waveN_bind(window, N)
        window[f'{self.__prefix_key}_wave{N}_sp_weight_enable_'].Update(disabled=value)
        for (sk, sp) in ([[
                            f'{self.__prefix_key}_wave{N}_character_{p}_skill_priority_',
                            f'{self.__prefix_key}_wave{N}_character_{p}_sp_weight_'
                          ] for p in pos]):
            window[sk].Widget.config(readonlybackground=('gray' if value else 'white'))
            if window[f'{self.__prefix_key}_wave{N}_sp_weight_enable_'].get():
                window[sp].Update(disabled=value)

    def w_sp_weight_enable_event(self, window: sg.Window, key: str, value: bool):
        N = key[5]
        self.quest['wave'][N]['sp_weight_enable'] = value
        for k in [f'{self.__prefix_key}_wave{N}_character_{p}_sp_weight_' for p in pos]:
            window[k].Update(disabled=(not value))

    def w_sp_weight_event(self, key: str, value: int):
        N = key[5]
        p = key[17:key.index('_', 17)]
        self.quest['wave'][N][f'character_{p}']['sp_weight'] = value

    def w_skill_priority_event(self, window: sg.Window, key: str, value: str):
        N = key[5]
        current_list = list(filter(lambda e: e != '', value.split(' > ')))
        available_list = [sk for sk in sk_list if sk not in current_list]
        current_list = priority_GUI('skill', key.replace('_', ' ').strip(), current_list, available_list, sk_list,
                                    window.mouse_location()).open()
        if current_list is not None:
            p = key[17:key.index('_', 17)]
            self.quest['wave'][N][f'character_{p}']['skill_priority'] = current_list if current_list != ['Same as Wave1'] else self.quest['wave']['1'][f'character_{p}']['skill_priority']  # noqa: E501
            window[f'{self.__prefix_key}{key}'].Update(' > '.join(self.quest['wave'][N][f'character_{p}']['skill_priority']))

    def w_total_event(self, window: sg.Window, new: int):
        w = self.quest['wave']
        old, w['total'] = w['total'], new

        if old > new:  # fewer
            for N in map(str, range(new + 1, old + 1)):
                window[f'{self.__prefix_key}_wave{N}_auto_'].hide_row()
                del w[N], window.AllKeysDict[f'{self.__prefix_key}_wave{N}_auto_']
                del window.AllKeysDict[f'{self.__prefix_key}_wave{N}_sp_weight_enable_']
                for p in pos:
                    del window.AllKeysDict[f'{self.__prefix_key}_wave{N}_character_{p}_skill_priority_'],
                    del window.AllKeysDict[f'{self.__prefix_key}_wave{N}_character_{p}_sp_weight_']
        elif old < new:
            uData.padding_wave(w)
            for N in map(str, range(old + 1, new + 1)):
                window.extend_layout(window[f'{self.__prefix_key}_wave_frame_'], self.__a_wave_row(w, N))

    def update_wave_id_status(self, window: sg.Window, w_id: int):
        window[f'{self.__prefix_key}_wave_status_'].Update(f'wave = {w_id} /')

    def update_loop_count_status(self, window: sg.Window, loop_count: int):
        window[f'{self.__prefix_key}_loop_count_status_'].Update(f'loop_count = {loop_count} of')

    def rename_title(self, window: sg.Window, exclude: List) -> Optional[str]:
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
        return json.dumps(self.quest, sort_keys=True) != json.dumps(self.__original_quest, sort_keys=True)

    def update_original_quest(self):
        self.__original_quest = deepcopy(self.quest)

    def reset(self, window: sg.Window):
        self.loop_count_status = self.quest['loop_count']
        self.wave_status = 1
        self.update_wave_id_status(window, self.wave_status)
        self.update_loop_count_status(window, self.loop_count_status)
