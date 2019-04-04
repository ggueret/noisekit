"""
Dummy audio classes, used on MacOS Mojave before the patching of portaudio.
https://github.com/ggueret/portaudio
"""
import itertools
import struct
from ..utils import noise_maker, compute_samples, sine_wave, grouper

paFloat32 = paInt16 = paInt32 = paInt24 = paInt8 = aUInt8 = None


def get_sample_size(format):
    return 2


class Stream(object):

    def __init__(self, pa_manager, rate, channels, format, input=False, output=False,
                 input_device_index=None, output_device_index=None, frames_per_buffer=1024,
                 start=True, input_host_api_specific_stream_info=None,
                 output_host_api_specific_stream_info=None, stream_callback=None):
        self.pa_manager = pa_manager
        self.rate = rate
        self.channels = channels
        self.format = format
        self.input = input
        self.output = output
        self.input_device_index = input_device_index
        self.output_device_index = output_device_index
        self.frames_per_buffer = frames_per_buffer
        self.start = start
        self.input_host_api_specific_stream_info = input_host_api_specific_stream_info
        self.output_host_api_specific_stream_info = output_host_api_specific_stream_info
        self.stream_callback = stream_callback
        self.sine_generator = sine_wave(20, framerate=self.rate, amplitude=0.5)

    def read(self, size, exception_on_overflow=True):
        max_amplitude = float(int((2 ** (2 * 8)) / 2) - 1)
        return b"".join([struct.pack("h", int(max_amplitude * next(self.sine_generator))) for i in range(size)])
#        channels = ((sine_wave(440, framerate=self.rate, amplitude=1),) for i in range(self.channels))
#        samples = compute_samples(channels, 2)
#        return self.get_frames(sine_wave(440, framerate=self.rate, amplitude=1), bufsize=1024)

#        frames = b''.join(b''.join(struct.pack('h', int(max_amplitude * sample)) for sample in channels) for channels in samples if channels is not None)
#        return "".join(list(noise_maker(size, framerate=self.rate, volume=32767)))


class PyAudio(object):

    def __init__(self):
        self.streams = []

    def open(self, *args, **kwargs):
        stream = Stream(self, *args, **kwargs)
        self.streams.append(stream)
        return stream

    def get_sample_size(self, format):
        return get_sample_size(format)
