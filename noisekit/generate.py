# code forked from zacharydenton/wavebender
import math
import wave
import numpy
import struct
from itertools import count, zip_longest, islice


def noise_maker(samples, framerate=44100.0, volume=32767.0):
    for i in range(samples):
        yield struct.pack("h", volume)


def grouper(n, iterable, fillvalue=None):
    "grouper(3, 'ABCDEFG', 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return zip_longest(fillvalue=fillvalue, *args)


def sine_wave(frequency=440, framerate=44100, amplitude=0.5, skip_frame=0):
    # https://dsp.stackexchange.com/questions/25119/generating-a-noisy-sine-wave-in-python-efficiently
    if amplitude > 1.0:
        amplitude = 1.0
    elif amplitude < 0.0:
        amplitude = 0.0

    for i in count(skip_frame):
#        sine = math.sin(2.0 * math.pi * float(frequency) * (float(i) / float(framerate)))
        sine = numpy.sin(2 * numpy.pi * float(frequency) * (float(i) / float(framerate)))
        yield float(amplitude) * sine
#        yield amplitude * sinusoid


def square_wave(frequency=440.0, framerate=44100, amplitude=0.5):
    for s in sine_wave(frequency, framerate, amplitude):
        if s > 0:
            yield amplitude
        elif s < 0:
            yield -amplitude
        else:
            yield 0.0


def damped_wave(frequency=440.0, framerate=44100, amplitude=0.5, length=44100):
    if amplitude > 1.0:
        amplitude = 1.0
    elif amplitude < 0.0:
        amplitude = 0.0

    return (math.exp(-(float(i % length) / float(framerate))) * s for i, s in enumerate(sine_wave(frequency, framerate, amplitude)))


def white_noise(amplitude=0.5):
    return numpy.random.normal(-1, 1, size=count(0))


def compute_samples(channels, nsamples=None):
    return islice(zip(*(map(sum, zip(*channel)) for channel in channels)), nsamples)


def write_wavefile(f, samples, nframes=None, nchannels=2, sampwidth=2, framerate=44100, bufsize=2048):
    if nframes is None:
        nframes = 0

    w = wave.open(f, 'wb')
    w.setparams((nchannels, sampwidth, framerate, nframes, 'NONE', 'not compressed'))

    max_amplitude = float(int((2 ** (sampwidth * 8)) / 2) - 1)

    # split the samples into chunks (to reduce memory consumption and improve performance)
    for chunk in grouper(bufsize, samples):
        frames = b''.join(b''.join(struct.pack('h', int(max_amplitude * sample)) for sample in channels) for channels in chunk if channels is not None)
        w.writeframesraw(frames)

    w.close()


def write_pcm(f, samples, sampwidth=2, framerate=44100, bufsize=2048):
    max_amplitude = float(int((2 ** (sampwidth * 8)) / 2) - 1)

    # split the samples into chunks (to reduce memory consumption and improve performance)
    for chunk in grouper(bufsize, samples):
        frames = b''.join(b''.join(struct.pack('h', int(max_amplitude * sample)) for sample in channels) for channels in chunk if channels is not None)
        f.write(frames)

    f.close()
