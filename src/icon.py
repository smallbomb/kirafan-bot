import cv2
import pyautogui
from os import path
from time import time, sleep
from typeguard import typechecked
from defined import Coord, Optional
from data import uData
from adb import adb


@typechecked
class Icon:
    def __init__(self, fname: str, confidence: float):
        self.name = fname[0:-4]
        self.path = path.join(uData.setting['img_dir'], fname)
        self.__confidence = confidence
        self.__region = uData.setting['game_region']
        self.__adb_use = uData.setting['adb']['use']
        if self.__adb_use:
            self.__IM_cache = cv2.imread(self.path, cv2.IMREAD_GRAYSCALE)
        self.__click = adb.click if self.__adb_use else pyautogui.click
        self.__locateCenterOnScreen = adb.locateCenterOnScreen if self.__adb_use else pyautogui.locateCenterOnScreen

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)

    def file_exist(self) -> bool:
        return path.isfile(self.path)

    def get_center(self, adb_update_cache: bool) -> Optional[Coord]:
        if not self.file_exist():
            return None

        if adb_update_cache:
            adb.set_update_cv2_IM_cache_flag()

        center = self.__locateCenterOnScreen(self.__IM_cache if self.__adb_use else self.path,
                                             region=self.__region,
                                             grayscale=True,
                                             confidence=self.__confidence)
        if center:
            x, y = center
            return (int(x), int(y))
        return center

    def found(self, adb_update_cache: bool = True) -> bool:
        return True if self.get_center(adb_update_cache) else False

    def click(self, times: int = 1, interval: float = uData.setting['sleep']['click'], adb_update_cache: bool = True) -> bool:
        if type(times) is not int:
            raise TypeError(f'type of argument "times" must be int; got {type(times).__qualname__} instead')
        coord = self.get_center(adb_update_cache)
        if coord:
            self.__click(*coord, times, interval)
            return True
        return False

    def scan(self, timeout: float = -1.0, cool_down: float = 0.2) -> bool:
        if timeout <= 0:
            return self.found(False)

        t0 = round(time(), 1)
        duration = 0
        while duration < timeout:
            if self.found():
                return True
            sleep(cool_down)
            duration = round(time(), 1) - t0
        return False


# Test
if __name__ == '__main__':
    icon = Icon("ok.png", 0.5)
    print(icon.scan(1))
