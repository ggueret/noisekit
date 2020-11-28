import datetime
import audioop
import shutil
import numpy
import wave
import os.path
import pytz

from .audio.input import InputConsumer

TIMEZONE = pytz.timezone("Europe/Paris")


class Monitor(InputConsumer):

    def __init__(self, service, settings, *args, **kwargs):
        super(Monitor, self).__init__(service, settings, *args, **kwargs)

    def run(self):

        seconds_per_buffer = self.settings["frames_per_buffer"] / self.settings["rate"]

        while not self.shutdown_flag.is_set():

            context = {}
            samples = self.listen(self.settings["frames_per_buffer"], threshold=self.settings["threshold"])
            tz_now = datetime.datetime.now(TIMEZONE)
            acquired_at = tz_now - datetime.timedelta(seconds=seconds_per_buffer * len(samples))

            filename = '/tmp/noisekit/{}.wav'.format(acquired_at.strftime("%Y%m%d-%H%M%S"))

            with wave.open(filename, "wb") as w:
                w.setnchannels(self.settings["channels"])
                w.setsampwidth(self.audio.get_sample_size(self.format_type))
                w.setframerate(self.settings["rate"])

                for sample in samples:
                    w.writeframesraw(sample)

            print("Writed", filename)
