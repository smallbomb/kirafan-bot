import cv2
import numpy as np
from os import path
from shutil import which
from subprocess import Popen, PIPE
from typeguard import typechecked
from time import sleep
from defined import RGB, Coord, Optional
from data import uData


@typechecked
def _shell_command(cmd: str):
    return Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)


@typechecked
class _Adb():
    def __init__(self):
        adb_path = path.normpath(uData.setting["adb"]["path"])
        adb_option = f'-s {uData.setting["adb"]["serial"]}' if len(uData.setting["adb"]["serial"]) > 0 else ''
        self.__offsetXY = uData.setting['game_region'][:2]
        self.__killserver_cmd = f'{adb_path} kill-server'
        self.__devices_cmd = f'{adb_path} devices'  # test adb daemon
        self.__tap_cmd = f'{adb_path} {adb_option} shell input tap'
        self.__sreencap_cmd = f'{adb_path} {adb_option} shell screencap'
        self.__swipe_cmd = f'{adb_path} {adb_option} shell input swipe'
        self.__stop_app = f'{adb_path} {adb_option} shell am force-stop com.aniplex.kirarafantasia'
        self.__start_app = f'{adb_path} {adb_option} shell monkey -p com.aniplex.kirarafantasia -c android.intent.category.LAUNCHER 1'  # noqa: E501
        self.__pixelformat = None
        self.__has_screenshot_IM = None
        self.__cv2_IM_COLOR_cache = None
        self.__cv2_IM_GRAY_cache = None
        if uData.setting["adb"]["use"] and which(adb_path) is None:
            if uData.setting['mode'].lower() == 'hotkey':
                raise FileNotFoundError(adb_path)
            else:
                print(f'Warnning: {adb_path} does not exist')

    def _screenshot(self, grayscale: bool = False):
        if self.__has_screenshot_IM:
            return self.__cv2_IM_GRAY_cache if grayscale else self.__cv2_IM_COLOR_cache

        img_bytes = None
        if self.__pixelformat is None:
            for i in range(2):
                _shell_command(self.__devices_cmd).communicate()
                out, err = _shell_command(self.__sreencap_cmd).communicate()
                if out:
                    break
                elif i == 0:
                    _shell_command(self.__killserver_cmd).communicate()
                else:
                    raise Exception(err.decode('utf8'))
            img_bytes = out.replace(b'\r\n', b'\n')
            self.__width = int.from_bytes(img_bytes[:4], byteorder='little')
            self.__height = int.from_bytes(img_bytes[4:8], byteorder='little')
            self.__pixelformat = int.from_bytes(img_bytes[8:12], byteorder='little')

        if self.__pixelformat == 1:  # RGBA
            img_bytes = img_bytes or _shell_command(self.__sreencap_cmd).stdout.read().replace(b'\r\n', b'\n')
            npbuffer = np.frombuffer(img_bytes[12:], dtype=np.uint8).reshape(self.__height, self.__width, 4)
            self.__cv2_IM_COLOR_cache = cv2.cvtColor(npbuffer, cv2.COLOR_RGBA2BGR)
            self.__cv2_IM_GRAY_cache = cv2.cvtColor(self.__cv2_IM_COLOR_cache, cv2.COLOR_BGR2GRAY)
        else:
            img_bytes = _shell_command(f'{self.__sreencap_cmd} -p').stdout.read().replace(b'\r\n', b'\n')
            self.__cv2_IM_COLOR_cache = cv2.imdecode(np.frombuffer(img_bytes, np.uint8), cv2.IMREAD_COLOR)
            self.__cv2_IM_GRAY_cache = cv2.cvtColor(self.__cv2_IM_COLOR_cache, cv2.COLOR_BGR2GRAY)

        self.__has_screenshot_IM = True
        return self.__cv2_IM_GRAY_cache if grayscale else self.__cv2_IM_COLOR_cache

    def set_update_cv2_IM_cache_flag(self):
        self.__has_screenshot_IM = False

    def click(self, x: int, y: int, clicks: int = 1, interval: float = 0.1):
        tap_cmd = f'{self.__tap_cmd} {x-self.__offsetXY[0]} {y-self.__offsetXY[1]}'
        for _ in range(clicks):
            _shell_command(tap_cmd)
            sleep(interval)

    def locateCenterOnScreen(self, needleIm: np.ndarray,
                             region,  # Do not use. just need this variable name.
                             grayscale: bool = False,
                             confidence: float = 0.999) -> Optional[Coord]:
        screenshotIm = self._screenshot(grayscale)
        needleIm_Height, needleIm_Width = needleIm.shape[:2]
        result = cv2.matchTemplate(screenshotIm, needleIm, cv2.TM_CCOEFF_NORMED)
        match_indices = np.arange(result.size)[(result > confidence).flatten()]
        matches = np.unravel_index(match_indices[:10000], result.shape)
        if len(matches[0]) == 0:
            return None

        matchx, matchy = matches[1], matches[0]
        points = []
        for x, y in zip(matchx, matchy):
            points.append((x, y, needleIm_Width, needleIm_Height))
            break

        if len(points) > 0:
            coord = points[0]
            return (int(coord[0]) + int(coord[2] / 2) + self.__offsetXY[0],
                    int(coord[1]) + int(coord[3] / 2) + self.__offsetXY[1])
        else:
            return None

    def pixelMatchesColor(self, x: int, y: int, expectedRGBColor: RGB, tolerance: int = 0) -> bool:
        r, g, b = self.getpixel(x, y)
        exR, exG, exB = expectedRGBColor[:3]
        return (abs(r - exR) <= tolerance) and (abs(g - exG) <= tolerance) and (abs(b - exB) <= tolerance)

    def getpixel(self, x: int, y: int) -> RGB:
        screenshotIm = self._screenshot()
        b, g, r = screenshotIm[y - self.__offsetXY[1], x - self.__offsetXY[0]]
        return (int(r), int(g), int(b))

    def swipe(self, x0: int, y0: int, x1: int, y1: int, duration: float = 0.0):
        _x0, _y0 = x0 - self.__offsetXY[0], y0 - self.__offsetXY[1]
        _x1, _y1 = x1 - self.__offsetXY[0], y1 - self.__offsetXY[1]
        pipe = _shell_command(f'{self.__swipe_cmd} {_x0} {_y0} {_x1} {_y1} {duration * 1000}')
        pipe.wait()

    def restart_app(self) -> bool:
        _shell_command(self.__stop_app).wait()
        _shell_command(self.__start_app).wait()
        return True

    def reload(self):
        self.__init__()

    def save_img(self, path: str):
        self.set_update_cv2_IM_cache_flag()
        im = self._screenshot()
        cv2.imwrite(path, im)


adb = _Adb()


# Test
if __name__ == '__main__':
    if which(uData.setting["adb"]["path"]) is None:
        raise FileNotFoundError(uData.setting["adb"]["path"])
    # coord = adb.locateCenterOnScreen(cv2.imread('img_1274x718/start_screen.png', cv2.IMREAD_GRAYSCALE), None, False, 0.8)
    # print(f'coord={coord}')
    # adb.click(*coord, 5, 0.2)
    adb.click(500, 500, 5, 0.2)
    # rgb = adb.getpixel(*coord)
    # print(f'RGB={rgb}')
    # adb.swipe(1168, 596, 1279, 596, 1)
