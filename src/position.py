import logging
import pyautogui
import threading
from sys import stdout
from typeguard import typechecked
from defined import Coord, Region
from data import uData


@typechecked
class Position:
    def __init__(self, id_: int):
        self.id = id_
        self.__init = True

    def __str__(self):
        if self.__init is True:
            return ""
        string = 'position{:02d}: (X,Y)=({:4d},{:4d}) RGB=({:3d},{:3d},{:3d}) Ratio({:.5f}, {:.5f})\n'
        return string.format(self.id, *self.coord, *self.rgb, *self.ratio)

    def record(self, preNewline: bool = False):
        x0, y0, width, height = uData.setting['game_region']
        x, y = pyautogui.position()
        self.coord = (x, y)
        self.rgb = pyautogui.screenshot().getpixel(self.coord)
        self.ratio = ((x - x0) / width, (y - y0) / height)
        msg = ('\n' if preNewline else '') + f'recode position{self.id:02}'
        logging.info(msg)
        self.__init = False


@typechecked
class Shot:
    def __init__(self, name: str, dpath: str, top_left: Coord, bottom_right: Coord):
        self.name = name
        self.dpath = dpath
        self.top_left = top_left
        self.bottom_right = bottom_right

    def screenshot(self):
        c1 = self.top_left
        c2 = self.bottom_right
        left, top, width, height = (c1[0], c1[1], c2[0] - c1[0], c2[1] - c1[1])
        logging.info(f'screenshot save {self.name} picture file to {self.dpath}')
        pyautogui.screenshot(self.dpath, region=(left, top, width, height))


@typechecked
def calc_region(top_left: Coord, bottom_right: Coord) -> Region:
    x0, y0 = top_left
    x1, y1 = bottom_right
    return (x0, y0, x1 - x0, y1 - y0)


def monitor_mode():
    print('Monitor mode: move mouse the out of game region to end...')
    thread = threading.currentThread()
    x0, y0, width, height = uData.setting['game_region']
    monitor_start = False
    while thread.is_running():
        x, y = pyautogui.position()
        out_of_region = (x < x0 or y < y0 or x >= x0 + width or y >= y0 + height)
        if monitor_start and out_of_region:
            break
        elif out_of_region:
            continue
        pix = pyautogui.screenshot(region=uData.setting['game_region']).getpixel((x - x0, y - y0))
        ratio = ((x - x0) / width, (y - y0) / height)
        pstr = 'position: (X,Y)=({:4d},{:4d}) RGB=({:3d},{:3d},{:3d}) Ratio({:.5f}, {:.5f})'.format(x, y, *pix, *ratio)
        print(pstr, end='')
        print('\b' * len(pstr), end='')
        stdout.flush()
        monitor_start = True
    print('\nmonitor mode end')


# Test
if __name__ == '__main__':
    pos = Position(1)
    pos.record()
