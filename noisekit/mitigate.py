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
from .audio.sound import SoundFile, SoundTone
from .utils import ChoiceIterator
from . import generate


class Mitigator(InputConsumer):

    PICKERS = {
        "cycle": cycle,
        "random": ChoiceIterator
    }

    def __init__(self, **kwargs):
        super(Mitigator, self).__init__(**kwargs)
        # todo: must handle the case where noisekit must exit from there
        self.producer = OutputProducer(player=kwargs.pop("player"), beat_every=kwargs.pop("beat_every"), beat_sound=kwargs.pop("beat_sound"))
        self.logger = get_logger(__name__)

        self.thresholds = {
            levels.LOW: kwargs.pop("low_threshold"),
            levels.MEDIUM: kwargs.pop("medium_threshold"),
            levels.HIGH: kwargs.pop("high_threshold")
        }

        self.sounds = {}
        picker = self.PICKERS[kwargs.pop("picking_mode")]

        for level in (levels.LOW, levels.MEDIUM, levels.HIGH):
            sounds = []

            for sound_path in kwargs.pop("{}_sounds".format(level.lower()), []):
                sounds.append(SoundFile(sound_path))

            if not sounds:
                sounds.append(SoundTone(
                    frequency=kwargs.pop("{}_frequency".format(level.lower())),
                    amplitude=0.5
                ))

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

            #  and context["frequency"] > 19
            if context["level"] is not levels.QUIET:
                context["staged"] = next(self.sounds[context["level"]])

            if context["staged"]:
                self.logger.info(f"{context['level']} level reached with {context['amplitude']} RMS @ {context['frequency']} Hz. Playing: '{context['staged']}'.")
                self.producer.enqueue(context["staged"])

            context["timestamp"] = time.time()

        self.producer.shutdown_flag.set()
        self.producer.join()
