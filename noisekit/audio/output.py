import time
import queue
import shlex
import threading
import subprocess
from .sound import SoundFile, SoundTone
from ..service import BaseThread


class OutputProducer(BaseThread):
    """A producer will spawn a player and pass it a queued sound bytes through a pipe"""

    def __init__(self, service, settings, *args, **kwargs):
        super().__init__(service, settings, *args, **kwargs)

        self.queue = queue.Queue()  # todo: consider queue.PriorityQueue() for level priority
        self.last_active = 0
        self.is_active = threading.Event()
        self.beat_sound = None

        if settings.get("beat_soundfile"):
            self.beat_sound = SoundFile(**settings["beat_soundfile"])

        elif settings.get("beat_soundtone"):
            self.beat_sound = SoundTone(**settings["beat_soundtone"])

        self.player_command = shlex.split(settings.get("player"))

    def enqueue(self, sound):
        self.queue.put_nowait(sound)

    def play(self, sound):
        self.is_active.set()
        self.last_active = time.time()

        process = subprocess.Popen(self.player_command, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT, stdin=subprocess.PIPE)

        for chunk in sound.read(1024):
            process.stdin.write(chunk)

        process.communicate()
        process.stdin.close()

        self.is_active.clear()

    def run(self):
        while not self.shutdown_flag.is_set():
            try:
                sound = self.queue.get(timeout=0.1)

            except queue.Empty:

                if self.settings["beat_every"] and self.beat_sound and time.time() - self.last_active >= self.settings["beat_every"]:
                    self.logger.info("beating with %s.", self.beat_sound)
                    self.play(self.beat_sound)

                continue

            if sound is None:
                break

            self.play(sound)
            self.queue.task_done()

        self.logger.debug("stopped the output producer.")
