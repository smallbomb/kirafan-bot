import os
import sys
if True:
    dir_path = os.path.dirname(os.path.realpath(__file__))
    parent_dir = os.path.abspath(os.path.join(dir_path, os.pardir + "/src"))
    sys.path.insert(0, parent_dir)
    from data import uData
    from hotkey import Hotkey


def test_data_format():
    assert type(uData.setting) == dict
    assert type(uData.gui_setting()) == dict
    assert uData.save_location(0, 31) is None
    assert uData.gui_setting()['location'] == [0, 31]


def test_hotkey():
    hotkey = Hotkey('rslmptcoxk')
    assert hotkey.safe_exit() is None
    assert hotkey._Hotkey__user_command('1') is None
    assert hotkey._Hotkey__user_command('r') is None
    assert hotkey._Hotkey__user_command('s') is None
    assert hotkey._Hotkey__user_command('l') is None
    # assert hotkey._Hotkey__user_command('m') is None
    assert hotkey._Hotkey__user_command('t') is None
    assert hotkey._Hotkey__user_command('c') is None
    assert hotkey._Hotkey__user_command('o') is None
    # assert hotkey._Hotkey__user_command('x') is None
    assert hotkey._Hotkey__user_command('k') is None
    assert hotkey.remove_all_hotkey() is None
