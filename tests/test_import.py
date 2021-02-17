import os
import sys
import inspect
current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
from data import uData
from window import square


def test_data_format():
    assert type(uData.setting) == dict


def test_square():
    square()
