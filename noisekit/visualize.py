import signal
import shutil
import audioop
import numpy

from termcolor import colored
from . import levels, config
from .logging import get_logger
from .audio import InputConsumer


class Visualizer(InputConsumer):

    def __init__(self, **kwargs):
        super(Visualizer, self).__init__(**kwargs)

        self.logger = get_logger(__name__)
        self.sensitivity = kwargs.pop("sensitivity")
        self.colors = {
            levels.QUIET: kwargs.pop("quiet_color"),
            levels.LOW: kwargs.pop("low_color"),
            levels.MEDIUM: kwargs.pop("medium_color"),
            levels.HIGH: kwargs.pop("high_color")
        }
        self.thresholds = {
            levels.LOW: kwargs.pop("low_threshold", self.rate + 1),
            levels.MEDIUM: kwargs.pop("medium_threshold", self.rate + 1),
            levels.HIGH: kwargs.pop("high_threshold", self.rate + 1)
        }
        self.symbols = {
            "amplitude": kwargs.pop("amplitude_symbol"),
            "frequency": kwargs.pop("frequency_symbol"),
            "peak": kwargs.pop("peak_symbol")
        }
        self.record_to = kwargs.pop("record")  # todo
        self.is_alive = None

    def stop(self, *args):
        self.is_alive = False

    def register_signals(self):
        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)

    def get_level(self, rms):
        for level in (levels.HIGH, levels.MEDIUM, levels.LOW):
            if rms >= self.thresholds[level]:
                return level
        return levels.QUIET

    def run(self):
        self.register_signals()

        self.logger.debug("Thresholds ~ {LOW}: %(LOW)i, {MEDIUM}: %(MEDIUM)i, {HIGH}: %(HIGH)s (RMS)".format(
            **{k: colored(k, v) for k, v in iter(self.colors.items())}), **self.thresholds)

        max_amplitude = numpy.iinfo(self.sample_format).max / self.sensitivity
        self.logger.debug("Max amplitude ~ {} RMS".format(max_amplitude))

        max_frequency = self.rate
        self.logger.debug("Max frequency ~ {} RMS".format(max_frequency))

        chunk_length = int((self.frames_per_buffer / self.rate) * 1000)
        self.logger.debug("Line duration ~ {:.2f} ms", chunk_length)

        max_value_length = max((len(str(max_frequency)), len(str(max_amplitude))))
        info_template = "{{frequency:{0}d}} Hz ~ RMS {{amplitude:<{0}d}}".format(max_value_length)

        self.is_alive = True

        last_frequency = 0

        while self.is_alive:

            context = {}
            samples = self.read(self.frames_per_buffer)

            context["amplitude"] = audioop.rms(samples, self.audio.get_sample_size(self.format_type))
            context["frequency"] = self.get_frequency(samples)
            context["level"] = self.get_level(context["amplitude"])

            infos = info_template.format(**context)
            max_bars = int((shutil.get_terminal_size((config.DEFAULT_TERM_WIDTH, None))[0] - len(infos) - 2) / 2)

            frequency_variation = abs(context["frequency"] - last_frequency)

            amplitude_bars = self.symbols["amplitude"] * int((context["amplitude"] * max_bars / max_amplitude))
            amplitude_bars = amplitude_bars or self.symbols["amplitude"]

            frequency_bars = self.symbols["frequency"] * int((frequency_variation * max_bars / (max_frequency * 2)))
            frequency_bars = frequency_bars or self.symbols["frequency"]

            if len(amplitude_bars) > max_bars:
                amplitude_bars = "{}{}".format(amplitude_bars[:max_bars - 1], self.peak_symbol)

            line_template = "{{:>{0}}} {{}} {{:<{0}}}".format(max_bars)

            print(colored(line_template.format(frequency_bars, infos, amplitude_bars), self.colors[context["level"]]))

            last_frequency = context["frequency"]
