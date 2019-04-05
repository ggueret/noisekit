import time
import audioop
import logging

from itertools import cycle
from . import levels, states
from .audio.input import InputConsumer
from .audio.output import OutputProducer
from .audio.sound import SoundFile, SoundTone
from .utils import ChoiceIterator


class Mitigator(InputConsumer):

    PICKERS = {
        "cycle": cycle,
        "random": ChoiceIterator
    }

    def __init__(self, service, settings, *args, **kwargs):
        super(Mitigator, self).__init__(service, settings, *args, **kwargs)
        # todo: must handle the case where noisekit must exit from there

        self.producer = OutputProducer(self.service, self.settings)
        self.logger = logging.getLogger(__name__)

        self.thresholds = {
            levels.LOW: settings["low_threshold"],
            levels.MEDIUM: settings["medium_threshold"],
            levels.HIGH: self.settings["high_threshold"]
        }

        self.sounds = {}
        picker = self.PICKERS[settings.get("picking_mode")]

        for level in (levels.LOW, levels.MEDIUM, levels.HIGH):
            sounds = []

            for soundfile in settings.get("{}_soundfiles".format(level.lower()), []):
                sounds.append(SoundFile(**soundfile))

            for soundtone in settings.get("{}_soundtones".format(level.lower()), []):
                sounds.append(SoundTone(**soundtone))

            self.sounds[level] = picker(sounds)

        self.record_to = self.settings["record"]  # todo
        self.is_quiet = None
        self.is_psycho = self.settings["psycho_mode"]
        self.last_block_playing = False

    def get_level(self, rms):
        for level in (levels.HIGH, levels.MEDIUM, levels.LOW):
            if rms >= self.thresholds[level]:
                return level
        return levels.QUIET

    def run(self):

        self.producer.start()

        self.logger.info("Mitigator is listening...")
        self.logger.debug("thresholds: low[%(LOW)i] medium[%(MEDIUM)i] high[%(HIGH)i]", self.thresholds)

        # one block duration in millisecond
        block_duration = int((self.settings["frames_per_buffer"] / self.settings["rate"]) * 1000)

        while not self.shutdown_flag.is_set() and self.producer.is_alive():
            context = {}
            context["state"] = states.REPLYING if self.producer.is_active.is_set() else states.LISTENING

            samples = self.read(self.settings["frames_per_buffer"])

            if context["state"] == states.REPLYING and not self.is_psycho:
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
                self.logger.info("%(level)s level reached with %(amplitude)i RMS @ %(frequency)i Hz. Playing: %(staged)s.", context)
                self.producer.enqueue(context["staged"])

            context["timestamp"] = time.time()

        self.producer.shutdown_flag.set()
        self.producer.join()
