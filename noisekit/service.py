import time
import signal
import logging
import threading


class Service(object):
    """Service act as a main thread"""

    def __init__(self, thread_obj, settings):
        self.thread = thread_obj(self, settings)
        self.logger = logging.getLogger(__name__)
        self.is_alive = None

    def run(self, latency=0.01):
        self.register_signals()
        self.is_alive = True

        self.thread.start()

        while self.is_alive:

            if not self.thread.is_alive():
                return  # PEP 479

            time.sleep(latency)

        self.thread.shutdown_flag.set()
        self.thread.join()

    def stop(self, *args):
        self.is_alive = False

    def register_signals(self):
        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)


class BaseThread(threading.Thread):
    """A thread is spawned by the `Service`, who pass himself with is settings"""

    def __init__(self, service, settings):
        super().__init__()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.service = service
        self.settings = settings
        self.shutdown_flag = threading.Event()
