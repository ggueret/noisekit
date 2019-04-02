import io
from .. import generate
from ..utils import chunked_read


class Sound(object):

    def read_chunks(self, size=None):
        raise NotImplementedError()


class SoundFile(Sound):

    def __init__(self, path):
        self.file_obj = open(path, "rb")

    def read_chunks(self, size=None):
        self.file_obj.seek(0)
        yield from chunked_read(self.file_obj, size)


class SoundTone(Sound):

    def __init__(self, amplitude=None, duration=None, frequency=None, waveform=None):
        self.amplitude = amplitude or 0.5
        self.frequency = frequency or 90
        self.duration = duration or 10
        self.waveform = waveform or "sine"

    def generate(self, f):
        channels = ((generate.square_wave(self.frequency, 44100, self.amplitude),) for i in range(1))
        samples = generate.compute_samples(channels, 44100 * self.duration)
        generate.write_wavefile(f, samples)

    def read_chunks(self, size=None):
        # todo: lru cache / disk cache
        file_obj = io.BytesIO()
        self.generate(file_obj)
        file_obj.seek(0)
        yield from chunked_read(file_obj, size)
