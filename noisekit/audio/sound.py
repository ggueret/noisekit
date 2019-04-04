import io
import time
from .. import generate
from ..logging import get_logger
from ..utils import chunked_read


class Sound(object):

    def __init__(self, fd=None, validate=True):
        self.fd = fd
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")

    def read(self, size=None):
        self.fd.seek(0)
        yield from chunked_read(self.fd, size)


class SoundFile(Sound):

    def __init__(self, path):
        super().__init__()
        self.logger.info("opening Sound file from %s...", path)
        self.fd = open(path, "rb")
        self.validate()

    def __str__(self):
        return f"SoundFile({self.path})"


class SoundTone(Sound):

    def __init__(self, amplitude=None, duration=None, frequency=None, rate=None, waveform=None):
        super().__init__()

        self.amplitude = amplitude or 0.5
        self.duration = duration or 3
        self.frequency = frequency or 90
        self.rate = rate or 44100
        self.waveform = waveform or "sine"

        self.fd = io.BytesIO()  # tones are generated on start and simply keeped into memory
        self.generate(self.fd)

    def generate(self, f):
        self.logger.debug("generating %s into memory...", self)
        func_start = time.time()
        channels = ((generate.square_wave(self.frequency, self.rate, self.amplitude),) for i in range(1))
        samples = generate.compute_samples(channels, self.rate * self.duration)
        generate.write_wavefile(f, samples)
        self.logger.debug("%s generated in %.2f seconds.", self, time.time() - func_start)

    def __str__(self):
        return f"SoundTone({self.waveform} - {self.frequency}Hz for {self.duration}s @ {int(self.amplitude*100)}%)"
