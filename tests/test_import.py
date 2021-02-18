import os
import sys
if True:
    dir_path = os.path.dirname(os.path.realpath(__file__))
    parent_dir = os.path.abspath(os.path.join(dir_path, os.pardir))
    sys.path.insert(0, parent_dir)
    from data import uData
    from main import main_job


def test_data_format():
    assert type(uData.setting) == dict
    assert main_job is None
