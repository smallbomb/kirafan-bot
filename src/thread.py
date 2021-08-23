import threading
from typeguard import typechecked


@typechecked
class Job(threading.Thread):
    def __init__(self, *args, **kwargs):
        super(Job, self).__init__(*args, **kwargs)
        self.__running = threading.Event()
        self.__running.set()
        self.__not_Pause = threading.Event()
        self.__not_Pause.set()

    def is_running(self):
        return self.__running.is_set()

    def is_pausing(self):
        return not self.__not_Pause.is_set()

    def wait(self):
        return self.__not_Pause.wait()

    def run(self):
        self._target(*self._args)

    def pause(self):
        self.__not_Pause.clear()

    def resume(self):
        self.__not_Pause.set()

    def stop(self):
        self.__not_Pause.set()
        self.__running.clear()
