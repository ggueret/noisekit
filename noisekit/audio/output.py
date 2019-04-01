import threading
import subprocess
from . import BaseThread


class OutputProducer(BaseThread):

    def __init__(self, queue):
        super().__init__()
        self.queue = queue

    def run(self):
        while not self.shutdown_flag.is_set():
            sound = self.queue.get()

            if sound is None:
                break

            #todo: use a formatter to get thread id
            self.logger.info("got sound into OutputProducer(%i): %s", threading.get_ident(), sound)
            self.queue.task_done()

        self.logger.info("stopped OutputProducer(%i).", threading.get_ident())
