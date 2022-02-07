import PySimpleGUI as sg
from typeguard import typechecked
from defined import List, Optional, Dict, Coord


@typechecked
class priority_GUI():
    def __init__(self, priority_type: str, text: str, current_list: List, available_list: List, default_list: List,
                 mouseXY: Coord):
        self.type = priority_type
        self.current_list = current_list
        self.available_list = available_list
        self.default_list = default_list
        self.stamina = self.__create_stamina_count_dict()
        self.layout = self.create_layout(text)
        self.window = sg.Window('kirafan-bot priority', self.layout, location=(mouseXY[0] - 240, mouseXY[1] - 190), modal=True)

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
            [sg.Submit('Submit'), sg.Cancel('Cancel')] +
            self.__skill_extend_button(text)
        ]

    def __stamina_extend(self) -> List:
        if self.type != 'stamina':
            return []
        layout = [sg.Text('count:')]
        for s, _elej in zip(self.default_list, ['left', 'center', 'right']):
            layout += [sg.Column([[sg.Text(s, pad=((5, 0), 5)),
                                   sg.Spin([i for i in range(1, 11)], readonly=True, initial_value=self.stamina[s], size=(2, 1), key=f'_stamina_count_{s}_', disabled=(s in self.available_list))]],  # noqa: E501
                                 expand_x=True, element_justification=_elej)]
        return layout

    def __skill_extend_button(self, text: str) -> List:
        if self.type == 'skill' and text[4] != '1':
            return [sg.Column([[sg.Button('Same as Wave1')]], expand_x=True, element_justification='right')]
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
            for s in self.default_list:
                self.window[f'_stamina_count_{s}_'].Update(disabled=(s in self.available_list))
