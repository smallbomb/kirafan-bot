
import PySimpleGUI as sg
from data import uData
from defined import Coord


def game_region() -> Coord:
    title_bar = sg.Column([[
                    sg.Column([[
                        sg.Text('game region', key='_grab1_', grab=True, font=('Helvetica', 12))
                    ]], pad=(0, 0)),
                    sg.Column([[
                        sg.Text('Ｘ', font=('Helvetica', 12, 'bold'), enable_events=True, key='_titlebar_close_')
                    ]], element_justification='r', k='_grab2_', expand_x=True, grab=True, pad=(0, 0))
               ]], expand_x=True, metadata='This window has a titlebar', pad=(0, 0))
    layout = [
        [title_bar],
        [sg.Graph(canvas_size=(1280, 720), graph_bottom_left=None, graph_top_right=None, background_color='red', pad=1)]
    ]

    sg.popup_ok('Tips: You can move window and click \'X\' to record new region', title='Tips')

    # (0, 40) => (0, 15)
    extra_y = 25
    _location = (uData.setting['game_region'][0], uData.setting['game_region'][1] - extra_y)

    window = sg.Window('', layout, location=_location,
                       keep_on_top=True, background_color='green2', no_titlebar=True, modal=True,
                       transparent_color='red',  grab_anywhere_using_control=False, finalize=True)
    window['_grab1_'].bind('<ButtonRelease-1>', '')
    window['_grab2_'].bind('<ButtonRelease-1>', '')
    while True:
        event, _ = window.read()
        if event is None:
            break
        _location = window.current_location(True)
        if event == '_titlebar_close_':
            break
    window.close()

    x, y = (_location[0], _location[1] + extra_y)
    status = _ck_region(x, y, *uData.setting['game_region'][2:])
    if status == 0:
        return (x, y)
    elif status == -1:
        cause = '.'
    elif status == -2:
        cause = ', please update home page ratio(advanced_setting.jsonc) or reselect game region.'

    sg.popup_error(f'Game region out of screen{cause}', title='Error')
    return uData.setting['game_region'][:2]


def _ck_region(x: int, y: int, width: int, height: int) -> int:
    screenwidth, screenheight = sg.Window.get_screen_size()
    if x < 0 or y < 0 or x + width > screenwidth or y + height > screenheight:
        return -1
    if uData.setting['crash_detection'] and not uData.setting['adb']['use'] and 'home_page' in uData.setting['ratio']:
        ratioX, ratioY = uData.setting['ratio']['home_page']['x'], uData.setting['ratio']['home_page']['y']
        if int(round(x + ratioX * width)) < 0 or int(round(y + ratioY * height)) < 0:
            return -2
    return 0
