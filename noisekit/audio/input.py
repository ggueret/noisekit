import numpy
import math
import audioop
import pyaudio
from collections import deque
from ..service import BaseThread


class InputConsumer(BaseThread):

    def __init__(self, service, settings, *args, **kwargs):
        super().__init__(service, settings, *args, **kwargs)

        self.format_type = getattr(pyaudio, "pa{}".format(settings["sample_format"]))
        self.audio = pyaudio.PyAudio()
        self.stream = self.audio.open(
            input=True,
            format=self.format_type,  # sample format
            channels=settings["channels"],  # fixme: must be passed from settings
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

    def listen(self, chuck_size, threshold, max_silence_time=1, max_silence_count=3):
        seconds_per_buffer = self.settings["frames_per_buffer"] / self.settings["rate"]
        previous_samples = deque(maxlen=math.ceil(1.0 / seconds_per_buffer))
        captured_samples = []

        is_acquiring = False
        silence_time = 0
        silence_count = 0

        while not self.shutdown_flag.is_set():

            sample = self.read(chuck_size)
            energy = audioop.rms(sample, self.audio.get_sample_size(self.format_type))

            if energy >= threshold:
                silence_time = 0
                is_acquiring = True
                captured_samples.append(sample)

            elif is_acquiring is True:
                silence_time += seconds_per_buffer
                if silence_time >= max_silence_time:
                    break

                captured_samples.append(sample)

            else:
                previous_samples.append(sample)

        if captured_samples:
            return list(previous_samples) + captured_samples


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
