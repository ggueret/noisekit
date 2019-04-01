import os
import time
import signal

import audioop
import tempfile
import subprocess

from itertools import cycle
from . import levels, states
from .logging import get_logger
from .audio.input import InputConsumer
from .audio.output import OutputProducer
from .utils import ChoiceIterator
from . import generate


class Mitigator(InputConsumer):

    PICKERS = {
        "cycle": cycle,
        "random": ChoiceIterator
    }

    def __init__(self, **kwargs):
        super(Mitigator, self).__init__(**kwargs)

        self.logger = get_logger(__name__)
        self.tempfiles = []

        self.producer = OutputProducer(beat_every=kwargs.pop("beat_every"), beat_sound=kwargs.pop("beat_sound"))

        self.thresholds = {
            levels.LOW: kwargs.pop("low_threshold"),
            levels.MEDIUM: kwargs.pop("medium_threshold"),
            levels.HIGH: kwargs.pop("high_threshold")
        }

        self.sounds = {}
        picker = self.PICKERS[kwargs.pop("picking_mode")]

        for level in (levels.LOW, levels.MEDIUM, levels.HIGH):
            sounds = kwargs.pop("{}_sounds".format(level.lower()), None)

            if not sounds:
                channels = ((generate.sine_wave(kwargs.pop("{}_frequency".format(level.lower())), 44100, 1.0),) for i in range(1))
                samples = generate.compute_samples(channels, 44100 * 10)

                tmp_file = tempfile.NamedTemporaryFile(delete=False)
                self.tempfiles.append(tmp_file.name)

                generate.write_wavefile(tmp_file.name, samples, 44100 * 10, 2, 16 // 8, 44100)
                self.logger.info("written sine wave for level %s, into '%s'", level, tmp_file.name)
                sounds = [tmp_file.name]

            self.sounds[level] = picker(sounds)

        self.record_to = kwargs.pop("record")  # todo
        self.is_quiet = None
        self.is_psycho = kwargs.pop("psycho_mode")
        self.last_block_playing = False

    def get_level(self, rms):
        for level in (levels.HIGH, levels.MEDIUM, levels.LOW):
            if rms >= self.thresholds[level]:
                return level
        return levels.QUIET

    def run(self):

        self.producer.start()

        self.logger.info(f"thresholds: low[{self.thresholds['LOW']}] medium[{self.thresholds['MEDIUM']}] high[{self.thresholds['HIGH']}]")

        while not self.shutdown_flag.is_set():

            context = {}
            context["state"] = states.PLAYING if self.producer.is_active.is_set() else states.LISTENING

            samples = self.read(self.frames_per_buffer)

            if context["state"] == states.PLAYING and not self.is_psycho:
                self.last_block_playing = True
                continue

            if self.last_block_playing:
                self.last_block_playing = False
                continue

            context["amplitude"] = audioop.rms(samples, self.audio.get_sample_size(self.format_type))
            context["frequency"] = self.get_frequency(samples)
            context["level"] = self.get_level(context["amplitude"])
            context["staged"] = None

            if context["level"] is not levels.QUIET and context["frequency"] > 19:
                context["staged"] = next(self.sounds[context["level"]])

            if context["staged"]:
                self.logger.info(f"{context['level']} level reached with {context['amplitude']} RMS @ {context['frequency']} Hz. Playing: '{context['staged']}'.")
                self.producer.enqueue({"path": context["staged"]})

            context["timestamp"] = time.time()

        self.producer.shutdown_flag.set()
        self.producer.join()

        # TODO: must be safer.
        for tmpfile in self.tempfiles:
            self.logger.info("remove temporary file: %s", tmpfile)
            os.unlink(tmpfile)
