import os
import sys
if True:
    dir_path = os.path.dirname(os.path.realpath(__file__))
    parent_dir = os.path.abspath(os.path.join(dir_path, os.pardir + "/src"))
    sys.path.insert(0, parent_dir)
    from data import uData
    from hotkey import Hotkey
    from main import check_basic_information


def test_data_format():
    assert type(uData.setting) == dict


def test_hotkey_and_mainfunc():
    if os.name == 'nt':
        hotkey = Hotkey('rslmptcoxk')
        assert hotkey.safe_exit() is None
        assert check_basic_information(hotkey) is None
