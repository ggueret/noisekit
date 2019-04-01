import wave
import numpy
import threading
import pyaudio
from .logging import get_logger


class BaseThread(threading.Thread):

    def __init__(self):
        super().__init__()
        self.shutdown_flag = threading.Event()


class InputConsumer(BaseThread):

    def __init__(self, **kwargs):
        super().__init__()
        self.rate = kwargs.pop("rate")
        self.frames_per_buffer = kwargs.pop("frames_per_buffer")
        self.channels = 1  # kwargs.pop("channels")
        self.sample_format = kwargs.pop("format")
        self.format_type = getattr(pyaudio, "pa{}".format(self.sample_format))
        self.no_overflow = kwargs.pop("no_overflow")

        self.audio = pyaudio.PyAudio()
        self.stream = self.audio.open(
            format=self.format_type,
            channels=self.channels,
            rate=self.rate, input=True,
            frames_per_buffer=self.frames_per_buffer
        )

#    def get_amplitude(self, samples):
#        data = numpy.fromstring(samples, self.sample_format)
#        return numpy.sqrt(numpy.mean(numpy.square(data)))

    def get_frequency(self, samples):
        window = numpy.hamming(self.frames_per_buffer)  # seems more accurate than blackman.
        data = numpy.fromstring(samples, self.sample_format) * window

        if not numpy.any(data):
            return 0

        fft = numpy.square(numpy.abs(numpy.fft.rfft(data)))
        maximum = fft[1:].argmax() + 1

        # quadratic interpolation around the max
        if maximum != len(fft) - 1:
            y0, y1, y2 = numpy.log(fft[maximum - 1:maximum + 2:])
            x1 = (y2 - y0) * .5 / (2 * y1 - y2 - y0)
            return int((maximum + x1) * self.rate / self.frames_per_buffer)

        return int(maximum * self.rate / self.frames_per_buffer)

    def read(self, length):
        return self.stream.read(length, exception_on_overflow=self.no_overflow)


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


class OutputProducer(BaseThread):

    def __init__(self, queue):
        super().__init__()
        self.queue = queue
        self.logger = get_logger(__name__)

    def run(self):
        while not self.shutdown_flag.is_set():
            sound = self.queue.get()

            if sound is None:
                break

            #todo: use a formatter to get thread id
            self.logger.info("got sound into OutputProducer(%i): %s", threading.get_ident(), sound)
            self.queue.task_done()

        self.logger.info("stopped OutputProducer(%i).", threading.get_ident())
