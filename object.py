import pyautogui
from time import time, sleep
from typeguard import typechecked
from defined import Coord, RGB, Ratio, Owner, Dict
from data import uData


@typechecked
class Object():
    def __init__(self,
                 coord_name: str, rgb_kname: str,
                 ratio: Ratio = (0.0, 0.0),
                 rgb: RGB = (0, 0, 0),
                 tolerance: int = 0):
        self.__region = uData.setting['game_region']
        self.__ratio = ratio  # relative position ratio by screen
        self.__tolerance = tolerance
        self.name = coord_name
        self.rgb_kname = rgb_kname
        self.coord = self.__calc_relative_pos()
        self.rgb = rgb

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)

    def found(self) -> bool:
        """return True or False
        """
        while True:
            try:
                return pyautogui.pixelMatchesColor(*self.coord, self.rgb, tolerance=self.__tolerance)
            except:
                sleep(0.2)

    def __calc_relative_pos(self) -> Coord:
        x0, y0, width, height = self.__region
        ratioX, ratioY = self.__ratio
        return (int(round(x0 + ratioX * width)), int(round(y0 + ratioY * height)))

    def moveTo(self):
        pyautogui.moveTo(*self.coord, uData.setting['mouse_duration_seconds'])

    def click(self, times: int = 1, interval: float = uData.setting['sleep']['click']):
        pyautogui.click(*self.coord, times, interval)
        sleep(interval)

    def click_sec(self, sec: float = 0.0, interval: float = 1.0):
        if sec <= 0:
            return
        duration = 0.0
        t0 = round(time(), 1)
        while duration < sec:
            pyautogui.click(*self.coord)
            if sec - duration >= interval:
                sleep(interval)
            else:
                sleep(sec - duration)
            duration = round(time(), 1) - t0
        pyautogui.click(*self.coord)


@typechecked
def Load_Objects(obj_name: Owner) -> Dict:
    objects = dict()
    for key in uData.setting['ratio'].keys():
        x, y, c_name, owner = uData.setting['ratio'][key].values()
        if obj_name not in owner + ['all']:
            continue
        ratio = (x, y)
        rgb, tolerance = uData.setting['color'][c_name].values() if c_name and c_name != "None" else [(0, 0, 0), 0]
        objects[key] = Object(key, c_name, ratio, tuple(rgb), tolerance)
    return objects


# Test
if __name__ == '__main__':
    obj = Object("sk", "ivory", (0.64634, 0.78623), (250, 250, 235), 25)
    print(obj)
    print(obj.click_sec(8))
