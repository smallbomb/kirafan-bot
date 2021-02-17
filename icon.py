import pyautogui
from os import path
from time import time, sleep
from typeguard import typechecked
from defined import Coord, Optional
from data import uData


@typechecked
class Icon:
    def __init__(self, fname: str, confidence: float, grayscale: bool = False):
        self.name = fname[0:-4]
        self.path = path.join(uData.setting['img_dir'], fname)
        self.__confidence = confidence
        self.__grayscale = grayscale
        self.__region = uData.setting['game_region']

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

        center = pyautogui.locateCenterOnScreen(self.path,
                                                region=self.__region,
                                                grayscale=self.__grayscale,
                                                confidence=self.__confidence)
        if center:
            x,y = center
            return (int(x),int(y))
        return center

    def found(self) -> bool:
        """
        return True or False
        """
        return True if self.get_center() else False

    def click(self, times: int = 1, interval: float = uData.setting['sleep']['click']) -> bool:
        coord = self.get_center()
        if coord:
            pyautogui.click(*coord, times, interval)
            return True
        return False

    # def scan_click(self, timeout: float = -1.0, not_found_click: bool = False, cool_down: float = 0.2) -> bool:
    #     if timeout <= 0:
    #         return self.click()
        
    #     t0 = round(time(), 1)
    #     duration = 0
    #     while duration < timeout:
    #         if self.click():
    #             return True
    #         if not_found_click: pyautogui.click()
    #         sleep(cool_down)
    #         duration = round(time(), 1) - t0
    #     return False

    def scan(self, timeout: float = -1.0, not_found_click: bool = False, cool_down: float = 0.2) -> bool:
        if timeout <= 0:
            return self.found()
        
        t0 = round(time(), 1)
        duration = 0
        while duration < timeout:
            if self.found():
                return True
            if not_found_click: pyautogui.click()
            sleep(cool_down)
            duration = round(time(), 1) - t0
        return False

# Test
if __name__ == '__main__':
    icon = Icon("ok.png", 0.5)
    print(icon.get_center())
