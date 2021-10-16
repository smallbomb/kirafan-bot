import pyautogui
from os import path
from time import time, sleep
from typeguard import typechecked
from defined import Coord, Optional
from data import uData
from adb import adb


@typechecked
class Icon:
    def __init__(self, fname: str, confidence: float, grayscale: bool = False):
        self.name = fname[0:-4]
        self.path = path.join(uData.setting['img_dir'], fname)
        self.__confidence = confidence
        self.__grayscale = grayscale
        self.__region = uData.setting['game_region']
        adb_use = uData.setting['adb']['use']
        self.__click = adb.click if adb_use else pyautogui.click
        self.__locateCenterOnScreen = adb.locateCenterOnScreen if adb_use else pyautogui.locateCenterOnScreen

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)

    def file_exist(self) -> bool:
        return path.isfile(self.path)

    def get_center(self) -> Optional[Coord]:
        """
        return None or Coord(x,y)
        """
        if not self.file_exist():
            return None

        center = self.__locateCenterOnScreen(self.path,
                                             region=self.__region,
                                             grayscale=self.__grayscale,
                                             confidence=self.__confidence)
        if center:
            x, y = center
            return (int(x), int(y))
        return center

    def found(self) -> bool:
        return True if self.get_center() else False

    def click(self, times: int = 1, interval: float = uData.setting['sleep']['click']) -> bool:
        coord = self.get_center()
        if coord:
            self.__click(*coord, times, interval)
            return True
        return False

    def scan(self, timeout: float = -1.0, cool_down: float = 0.2) -> bool:
        if timeout <= 0:
            return self.found()

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
