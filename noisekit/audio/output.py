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

    def __init__(self, queue):
        super().__init__()
        self.queue = queue
        self.is_playing = threading.Event()  # todo: replace by is_active.

    def run(self):
        while not self.shutdown_flag.is_set():
            sound = self.queue.get()

            if sound is None:
                break

            #todo: use a formatter to get thread id
            self.logger.info("got sound into OutputProducer(%i): %s", threading.get_ident(), sound)

            self.is_playing.set()
#            process = subprocess.Popen(["afplay", sound["path"]], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
#            process.communicate()
#
            process = subprocess.Popen(["/Applications/VLC.app/Contents/MacOS/VLC", "--play-and-exit", "-"], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT, stdin=subprocess.PIPE)

            # pipe can be broken
            with open(sound["path"], "rb") as f:
                for chunk in read_in_chunks(f):
                    process.stdin.write(chunk)

            process.communicate()
            process.stdin.close()

            self.is_playing.clear()
            self.queue.task_done()

        self.logger.info("stopped OutputProducer(%i).", threading.get_ident())
