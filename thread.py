import logging
import threading
from time import sleep
from typeguard import typechecked
from datetime import datetime
from data import uData


@typechecked
def wait_until(clock: str):
    def to_hour(s: float) -> int:
        return int(s / 3600) % 24

    def to_min(s: float) -> str:
        return int(s / 60) % 60

    def to_sec(s: float) -> int:
        return int(s) % 60

    clock = datetime.now().strftime("%Y-%m-%d") + "T" + clock
    next_time = datetime.strptime(clock, "%Y-%m-%dT%H:%M:%S")
    log_t = datetime.fromtimestamp(0)
    while True:
        now_time = datetime.now()
        wait_s = round((next_time - now_time).total_seconds(), 1)
        if wait_s < 0:
            break
        if (now_time - log_t).total_seconds() > 60:
            logging.info("倒數: {:02d}時 {:02d}分 {:02d}秒, 現在時間: {:s} 設置時間: {:s}".format(to_hour(wait_s), to_min(wait_s), to_sec(wait_s), now_time.strftime("%H:%M:%S"), next_time.strftime("%H:%M:%S")))
            log_t = now_time
        sleep(wait_s / 2)


@typechecked
class Job(threading.Thread):
    def __init__(self, *args, **kwargs):
        super(Job, self).__init__(*args, **kwargs)
        self.__running = threading.Event()
        self.__running.set()
        self.__not_Pause = threading.Event()
        self.__not_Pause.set()
        self.__timer = self.set_timer(uData.setting['set_timer'])

    def is_running(self):
        return self.__running.is_set()

    def is_pause(self):
        return self.__not_Pause.wait()

    def run(self):
        if self.__timer:
            logging.info('set_timer = {}'.format(self.__timer))
            wait_until(self.__timer)
            self.__timer = None
        self._target(*self._args)

    def pause(self):
        self.__not_Pause.clear()

    def resume(self):
        self.__not_Pause.set()

    def stop(self):
        self.__not_Pause.set()
        self.__running.clear()

    def set_timer(self, timer: dict):
        if timer['used']:
            self.__timer = timer['time']
