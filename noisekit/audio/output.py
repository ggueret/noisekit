import time
import queue
import threading
import subprocess
from . import BaseThread


def read_in_chunks(file_obj, chunk_size=1024):
    while True:
        chunk = file_obj.read(chunk_size)

        if not chunk:
            return

        yield chunk


class Sound(object):

    def __init__(self, path=None, *args, **kwargs):
        self.path = path

    def open(self):
        with open(self.path, "rb") as f:
            return f


class OutputProducer(BaseThread):

    def __init__(self, queue, beat_every=None, beat_sound=None):
        super().__init__()
        self.queue = queue
        self.last_active = 0
        self.is_active = threading.Event()

        self.beat_every = beat_every
        self.beat_sound = beat_sound

    def play(self, sound):

        self.is_active.set()
        self.last_active = time.time()
        process = subprocess.Popen(["/Applications/VLC.app/Contents/MacOS/VLC", "--play-and-exit", "-"], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT, stdin=subprocess.PIPE)

        with open(sound["path"], "rb") as f:
            for chunk in read_in_chunks(f):
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

            #todo: use a formatter to get thread id
            self.logger.info("got sound into OutputProducer(%i): %s", threading.get_ident(), sound)

            self.play(sound)
            self.queue.task_done()

        self.logger.info("stopped OutputProducer(%i).", threading.get_ident())
