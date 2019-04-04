import numpy
import pyaudio
from ..service import BaseThread


class InputConsumer(BaseThread):

    def __init__(self, service, settings, *args, **kwargs):
        super().__init__(service, settings, *args, **kwargs)

        self.format_type = getattr(pyaudio, "pa{}".format(settings["sample_format"]))
        self.audio = pyaudio.PyAudio()
        self.stream = self.audio.open(
            input=True,
            format=self.format_type,  # sample format
            channels=1,  # fixme: must be passed from settings
            rate=settings["rate"],
            frames_per_buffer=settings["frames_per_buffer"]
        )

    def get_frequency(self, samples):
        window = numpy.hamming(self.settings["frames_per_buffer"])  # seems more accurate than blackman.
        data = numpy.fromstring(samples, self.settings["sample_format"]) * window

        if not numpy.any(data):
            return 0

        fft = numpy.square(numpy.abs(numpy.fft.rfft(data)))
        maximum = fft[1:].argmax() + 1

        # quadratic interpolation around the max
        if maximum != len(fft) - 1:
            y0, y1, y2 = numpy.log(fft[maximum - 1:maximum + 2:])
            x1 = (y2 - y0) * .5 / (2 * y1 - y2 - y0)
            return int((maximum + x1) * self.settings["rate"] / self.settings["frames_per_buffer"])

        return int(maximum * self.rate / self.settings["frames_per_buffer"])

    def read(self, length):
        return self.stream.read(length, exception_on_overflow=self.settings["no_overflow"])


class Recorder(object):

    def __init__(self, fp, channels, framerate, format_type):
        self.output = wave.open(fp)
        self.wave.setnchannels(channels)
        self.wave.setsampwidth(pyaudio.get_sample_size(format_type))
        self.wave.setframerate(framerate)

    def write(self, data):
        return self.wave.writeframes(data)

    def __exit__(self):
        self.wave.close()
