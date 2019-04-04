import shutil
import audioop
import numpy

from termcolor import colored
from . import levels, config
from .logging import get_logger
from .audio.input import InputConsumer


class Visualizer(InputConsumer):

    def __init__(self, service, settings, *args, **kwargs):
        super(Visualizer, self).__init__(service, settings, *args, **kwargs)

        self.colors = {
            levels.QUIET: settings["quiet_color"],
            levels.LOW: settings["low_color"],
            levels.MEDIUM: settings["medium_color"],
            levels.HIGH: settings["high_color"]
        }
        self.thresholds = {
            levels.LOW: settings.get("low_threshold", self.settings["rate"] + 1),
            levels.MEDIUM: settings.get("medium_threshold", self.settings["rate"] + 1),
            levels.HIGH: settings.get("high_threshold", self.settings["rate"] + 1)
        }
        self.symbols = {
            "amplitude": settings["amplitude_symbol"],
            "frequency": settings["frequency_symbol"],
            "peak": settings["peak_symbol"]
        }

    def get_level(self, rms):
        for level in (levels.HIGH, levels.MEDIUM, levels.LOW):
            if rms >= self.thresholds[level]:
                return level
        return levels.QUIET

    def run(self):

        self.logger.debug("Thresholds ~ {LOW}: %(LOW)i, {MEDIUM}: %(MEDIUM)i, {HIGH}: %(HIGH)s (RMS)".format(
            **{k: colored(k, v) for k, v in iter(self.colors.items())}), **self.thresholds)

        max_amplitude = numpy.iinfo(self.settings["sample_format"]).max / self.settings["sensitivity"]
        self.logger.debug("Max amplitude ~ {} RMS".format(max_amplitude))

        max_frequency = self.settings["rate"]
        self.logger.debug("Max frequency ~ {} RMS".format(max_frequency))

        chunk_length = int((self.settings["frames_per_buffer"] / self.settings["rate"]) * 1000)
        self.logger.debug("Line duration ~ {:.2f} ms", chunk_length)

        max_value_length = max((len(str(max_frequency)), len(str(max_amplitude))))
        info_template = "{{frequency:{0}d}} Hz ~ RMS {{amplitude:<{0}d}}".format(max_value_length)

        last_frequency = 0

        while not self.shutdown_flag.is_set():

            context = {}
            samples = self.read(self.settings["frames_per_buffer"])

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
