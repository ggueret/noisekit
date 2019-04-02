import time
import queue
import shlex
import threading
import subprocess
from . import BaseThread
from .sound import SoundFile


class OutputProducer(BaseThread):
    """A producer will spawn a player and pass it a queued sound bytes through a pipe"""

    def __init__(self, player, beat_every=None, beat_sound=None):
        super().__init__()
        self.queue = queue.Queue()  # todo: consider queue.PriorityQueue() for level priority
        self.last_active = 0
        self.is_active = threading.Event()

        self.beat_every = beat_every
        self.beat_sound = SoundFile(beat_sound)

        self.player_command = shlex.split(player)

    def enqueue(self, sound):
        self.queue.put_nowait(sound)

    def play(self, sound):

        self.is_active.set()
        self.last_active = time.time()

        # todo: propagate if a FileNotFoundError is raised for eg. a misconfigured player
        process = subprocess.Popen(self.player_command, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT, stdin=subprocess.PIPE)

        for chunk in sound.read_chunks():
            process.stdin.write(chunk)
#            process.stdin.flush()

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
                    self.play(self.beat_sound)
                continue

            if sound is None:
                break

            self.play(sound)
            self.queue.task_done()

        self.logger.info("stopped Output Producer.")
