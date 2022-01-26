import os
import sys
if True:
    dir_path = os.path.dirname(os.path.realpath(__file__))
    parent_dir = os.path.abspath(os.path.join(dir_path, os.pardir + "/src"))
    sys.path.insert(0, parent_dir)
    from data import uData
    from hotkey import Hotkey
    from gui import kirafanbot_GUI


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


def test_gui():
    kirafanbot_gui = kirafanbot_GUI()
    tab = kirafanbot_gui.find_tab_by_name('example')
    testing = {'_0_example_loop_count_setting_': '54', '_0_example_crea_stop_': True, '_0_example_stamina_use_': False,
               '_0_example_orb_name_': '5566', '_0_example_orb1_use_': False, '_0_example_orb1_wave_N_': 5,
               '_0_example_orb1_myturn_': 10, '_0_example_orb1_target_': 'B', '_0_example_friend_support_use_': True,
               '_0_example_friend_support_wave_N_': 5, '_0_example_friend_support_myturn_': 10,
               '_0_example_friend_support_replace_': 'character_right', '_0_example_wave_total_': 5,
               '_0_example_wave1_auto_': False, '_0_example_wave1_sp_weight_enable_': True,
               '_0_example_wave1_character_left_sp_weight_': 4, '_0_example_wave1_character_middle_sp_weight_': 6,
               '_0_example_wave1_character_right_sp_weight_': 8, '_adb_use_': True}
    for k in testing.keys():
        kirafanbot_gui.handle_tab_event(tab, k, testing)
        kirafanbot_gui.handle_adb_event(k, testing[k])
    uData.reload()

    assert kirafanbot_gui.find_tab_by_key('_0_example_orb1_use_') is not None
    assert tab is not None
    assert uData.setting['loop_count'] == 54
    assert uData.setting['crea_stop'] is True
    assert uData.setting['stamina']['use'] is False
    assert uData.setting['orb']['orb_name'] == '5566'
    assert uData.setting['orb']['1']['use'] is False
    assert uData.setting['orb']['1']['wave_N'] == 5
    assert uData.setting['orb']['1']['myturn'] == 10
    assert uData.setting['orb']['1']['target'] == 'B'
    assert uData.setting['friend_support']['use'] is True
    assert uData.setting['friend_support']['wave_N'] == 5
    assert uData.setting['friend_support']['myturn'] == 10
    assert uData.setting['friend_support']['replace'] == 'character_right'
    assert uData.setting['wave']['total'] == 5
    assert uData.setting['wave']['1']['auto'] is False
    assert uData.setting['wave']['1']['sp_weight_enable'] is True
    assert uData.setting['wave']['1']['character_left']['sp_weight'] == 4
    assert uData.setting['wave']['1']['character_middle']['sp_weight'] == 6
    assert uData.setting['wave']['1']['character_right']['sp_weight'] == 8
    assert uData.setting['adb']['use'] is True
