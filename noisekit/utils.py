import os.path
import math
import struct
import itertools
from random import choice
from collections import deque

try:
    from itertools import zip_longest
except ImportError:
    from itertools import izip_longest as zip_longest


def chunked_read(file_obj, size=None):
    while True:
        chunk = file_obj.read(1024 if size is None else size)

        if not chunk:
            return

        yield chunk


class ChoiceIterator(object):

    def __init__(self, values):
        self.__values = values

    def __iter__(self):
        return self

    def __next__(self):
        return choice(self.__values)


class MovingAverage(object):

    def __init__(self, size):
        self.__size = size
        self.__sum = 0
        self.__q = deque([])

    def next(self, val):
        if len(self.__q) == self.__size:
            self.__sum -= self.__q.popleft()
        self.__sum += val
        self.__q.append(val)
        return 1.0 * self.__sum / len(self.__q)


def absdir(path):
    return os.path.abspath(os.path.dirname(__file__))


def sine_wave(frequency=440.0, framerate=44100, amplitude=0.5, skip_frame=0):
    if amplitude > 1.0:
        amplitude = 1.0

    elif amplitude < 0.0:
        amplitude = 0.0

    for i in itertools.count(skip_frame):
        sine = math.sin(2.0 * math.pi * float(frequency) * (float(i) / float(framerate)))
        yield float(amplitude) * sine


def grouper(n, iterable, fillvalue=None):
    "grouper(3, 'ABCDEFG', 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return zip_longest(fillvalue=fillvalue, *args)


def compute_samples(channels, nsamples=None):
    return itertools.islice(zip(*(map(sum, zip(*channel)) for channel in channels)), nsamples)


def noise_maker(samples, framerate=44100.0, volume=32767.0):
    for i in range(samples):
        yield struct.pack("h", volume)
