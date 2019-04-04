import time
import signal
from .logging import get_logger


class Service(object):

    def __init__(self, thread_obj, settings):
        self.cache = None
        self.thread = thread_obj(self, settings)
        self.logger = get_logger(__name__)
        self.is_alive = None

    def run(self, latency=0.01):
        self.register_signals()
        self.is_alive = True

        self.thread.start()

        while self.is_alive:
            time.sleep(latency)

        self.thread.shutdown_flag.set()
        self.thread.join()

    def stop(self, *args):
        self.is_alive = False

    def register_signals(self):
        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)
