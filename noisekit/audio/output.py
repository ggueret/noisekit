import time
import queue
import threading
import subprocess
from . import BaseThread
from ..utils import chunked_read


class Sound(object):

    def __init__(self, path=None, *args, **kwargs):
        self.path = path

    def open(self):
        with open(self.path, "rb") as f:
            return f


class OutputProducer(BaseThread):
    """A producer will spawn a player and pass it a queued sound bytes through a pipe"""

    def __init__(self, beat_every=None, beat_sound=None):
        super().__init__()
        self.queue = queue.Queue()  # todo: consider queue.PriorityQueue() for level priority
        self.last_active = 0
        self.is_active = threading.Event()

        self.beat_every = beat_every
        self.beat_sound = beat_sound

    def enqueue(self, sound):
        self.queue.put_nowait(sound)

    def play(self, sound):

        self.is_active.set()
        self.last_active = time.time()
        process = subprocess.Popen(["/Applications/VLC.app/Contents/MacOS/VLC", "--play-and-exit", "-"], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT, stdin=subprocess.PIPE)

        with open(sound["path"], "rb") as f:
            for chunk in chunked_read(f):
                process.stdin.write(chunk)

        process.communicate()
        process.stdin.close()

        self.is_active.clear()

    def run(self):
        while not self.shutdown_flag.is_set():
            try:
                sound = self.queue.get(timeout=0.1)

            except queue.Empty:
                if self.beat_every and time.time() - self.last_active >= self.beat_every:
                    self.logger.info("beating.")
                    self.play({"path": self.beat_sound})
                continue

            if sound is None:
                break

            self.play(sound)
            self.queue.task_done()

        self.logger.info("stopped Output Producer.")
