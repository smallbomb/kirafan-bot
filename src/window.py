
import PySimpleGUI as sg
from data import uData
from defined import Coord


def game_region() -> Coord:
    title_bar = sg.Column([[
                    sg.Column([[
                        sg.Text('game region', grab=True, font=('Helvetica', 12))
                    ]], pad=(0, 0)),
                    sg.Column([[
                        sg.Text('Ｘ', font=('Helvetica', 12, 'bold'), enable_events=True, key='_titlebar_close_')
                    ]], element_justification='r', expand_x=True, grab=True, pad=(0, 0))
               ]], expand_x=True, grab=True, metadata='This window has a titlebar', pad=(0, 0))
    layout = [
        [title_bar],
        [sg.Graph(canvas_size=(1280, 720), graph_bottom_left=None, graph_top_right=None, background_color='red', pad=1)]
    ]

    # (0, 40) => (0, 15)
    window = sg.Window('', layout, location=(uData.setting['game_region'][0], uData.setting['game_region'][1] - 25),
                       keep_on_top=True, background_color='green2', no_titlebar=True, return_keyboard_events=True,
                       modal=True, transparent_color='red',  grab_anywhere_using_control=False)

    sg.popup_ok('You can move window.\nIf game region is fine, please click \'X\' to close window')
    window.read()
    location = window.current_location(True)
    window.close()
    return (location[0], location[1] + 25)
