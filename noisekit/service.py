import time
import signal
from .logging import get_logger


class Service(object):

    def __init__(self, thread):
        self.thread = thread
        self.is_alive = None
        self.logger = get_logger(__name__)

    def run(self, latency=0.01):
        self.register_signals()
        self.is_alive = True

        self.thread.start()

        while self.is_alive:
            time.sleep(latency)

        self.logger.info("waiting for related thread(s) to finish...")
        self.thread.shutdown_flag.set()
        self.thread.join()

    def stop(self, *args):
        self.is_alive = False

    def register_signals(self):
        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)
