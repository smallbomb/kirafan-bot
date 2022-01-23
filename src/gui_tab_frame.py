import re
import json
import PySimpleGUI as sg
from copy import deepcopy
from typeguard import typechecked
from defined import List, Optional, Dict
from gui_priority import priority_GUI
_tab_handle_re = re.compile(r'^_(loop_count_setting|stamina|orb|wave).*_$')


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
            self.__info_modify(),
            self.__crea_stop(),
            self.__loop_count(),
            self.__stamina_area(),
            self.__orb_area(),
            self.__wave_area()
        ]

    def __info_modify(self) -> List:
        return [
            sg.Input(self.name, key=f'{self.__prefix_key}_title_', size=20),
            sg.Button('Rename', key=f'{self.__prefix_key}_rename_', size=6, mouseover_colors=None),
            sg.Button('Delete', key=f'{self.__prefix_key}_delete_', size=6, mouseover_colors=None)
        ]

    def __crea_stop(self) -> List:
        k = [f'{self.__prefix_key}_crea_stop_']
        return [
            sg.Checkbox('crea_stop', key=k[0], default=self.quest['crea_stop'], enable_events=True)
        ]

    def __loop_count(self) -> List:
        k = [f'{self.__prefix_key}_loop_count_status_', f'{self.__prefix_key}_loop_count_setting_']
        return [
            sg.Text(f'loop_count = {self.loop_count_status} of', key=k[0]),
            sg.Input(self.quest['loop_count'], key=k[1], size=(3, 1), pad=0, enable_events=True)
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

    def __wave_area(self) -> List:
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

    def update_all_bind(self, window: sg.Window):
        for N in map(str, range(1, self.quest['wave']['total'] + 1)):
            self.update_waveN_bind(window, N)
        self.update_stamina_bind(window)

    def update_waveN_bind(self, window: sg.Window, N: str):
        for p in ['left', 'middle', 'right']:
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
            'stamina': lambda window, key, value: self.handle_stamina_event(window, key, value),
            'orb': lambda window, key, value: self.handle_orb_event(window, key, value),
            'wave': lambda window, key, value: self.handle_wave_event(window, key, value)
        }
        key = event[len(self.__prefix_key):]
        matchresult = _tab_handle_re.match(key)
        if matchresult:
            _handle_map[matchresult[1]](window, key, values[event])

    def handle_stamina_event(self, window: sg.Window, key: str, value):
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

    def handle_wave_event(self, window: sg.Window, key: str, value):
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
