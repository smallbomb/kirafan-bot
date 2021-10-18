import cv2
import numpy as np
from os import path
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
        self.__tap_cmd = f'{adb_path} {adb_option} shell input tap'
        self.__sreencap_cmd = f'{adb_path} {adb_option} shell screencap'
        self.__swipe_cmd = f'{adb_path} {adb_option} shell input swipe'
        self.__stop_app = f'{adb_path} {adb_option} shell am force-stop com.aniplex.kirarafantasia'
        self.__start_app = f'{adb_path} {adb_option} shell monkey -p com.aniplex.kirarafantasia -c android.intent.category.LAUNCHER 1'  # noqa: E501
        self.__pixelformat = None
        self.__offsetXY = uData.setting['game_region'][:2]

    def _screenshot(self, grayscale: bool = False):
        img_bytes = None
        if self.__pixelformat is None:
            out, err = _shell_command(self.__sreencap_cmd).communicate()
            if err:
                raise Exception(err.decode('utf8'))
            img_bytes = out.replace(b'\r\n', b'\n')
            self.__width = int.from_bytes(img_bytes[:4], byteorder='little')
            self.__height = int.from_bytes(img_bytes[4:8], byteorder='little')
            self.__pixelformat = int.from_bytes(img_bytes[8:12], byteorder='little')

        if self.__pixelformat == 1:  # RGBA
            img_bytes = img_bytes or _shell_command(self.__sreencap_cmd).stdout.read().replace(b'\r\n', b'\n')
            img_bytes = img_bytes[12:]
            npbuffer = np.frombuffer(img_bytes, dtype=np.uint8)
            npbuffer = npbuffer.reshape(self.__height, self.__width, 4)
            if grayscale:
                return cv2.cvtColor(npbuffer, cv2.COLOR_RGBA2GRAY)
            else:
                return cv2.cvtColor(npbuffer, cv2.COLOR_RGBA2BGR)
        else:
            img_bytes = _shell_command(f'{self.__sreencap_cmd} -p').stdout.read().replace(b'\r\n', b'\n')
            if grayscale:
                return cv2.imdecode(np.frombuffer(img_bytes, np.uint8), cv2.IMREAD_GRAYSCALE)
            else:
                return cv2.imdecode(np.frombuffer(img_bytes, np.uint8), cv2.IMREAD_COLOR)

    def click(self, x: int, y: int, clicks: int = 1, interval: float = 0.0):
        tap_cmd = f'{self.__tap_cmd} {x-self.__offsetXY[0]} {y-self.__offsetXY[1]}'
        pipes = []
        for _ in range(clicks):
            pipe = _shell_command(tap_cmd)
            pipes.append(pipe)
            sleep(interval)

        for p in pipes:
            p.wait()

    def locateCenterOnScreen(self, path: str, region, grayscale: bool = False, confidence: float = 0.999) -> Optional[Coord]:
        screenshotIm = self._screenshot(grayscale)
        needleIm = cv2.imread(path, cv2.IMREAD_COLOR if grayscale is False else cv2.IMREAD_GRAYSCALE)
        needleIm_Height, needleIm_Width = needleIm.shape[:2]
        result = cv2.matchTemplate(needleIm, screenshotIm, cv2.TM_CCOEFF_NORMED)
        match_indices = np.arange(result.size)[(result > confidence).flatten()]
        matches = np.unravel_index(match_indices[:10000], result.shape)
        if len(matches[0]) == 0:
            return None

        # use a generator for API consistency:
        matchx, matchy = matches[1], matches[0]
        points = []
        for x, y in zip(matchx, matchy):
            points.append((x, y, needleIm_Width, needleIm_Height))

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


adb = _Adb()


# Test
if __name__ == '__main__':
    # coord = adb.locateCenterOnScreen('img_1274x718/start.png', False, 0.8)
    # print(f'coord={coord}')
    # adb.click(*coord, 5, 0.2)
    adb.click(500, 500, 5, 0.2)
    # rgb = adb.getpixel(*coord)
    # print(f'RGB={rgb}')
    # adb.swipe(1168, 596, 1279, 596, 1)
