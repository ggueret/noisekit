"""
"""
from __future__ import absolute_import
import re
import os
import json
import platform
import argparse
import logging

from . import __DESCRIPTION__, __VERSION__
from .service import Service
from .audio.sound import WAVE_GENERATORS


def setup_logging(level):
    level_value = getattr(logging, level.upper())
    format_tpl = "[%(levelname)s] ~ %(message)s"

    # in runned by systemd, there is no reason to display datetime to syslog
    if os.getppid() != 1:
        format_tpl = "%(asctime)s " + format_tpl

    logging.basicConfig(level=level_value, format=format_tpl, datefmt="%Y-%m-%d %H:%M:%S")


def load_settings(args):
    """Load settings using in order: config > envion > argv"""
    merged_config = {}
    file_config = json.load(args.config) if args.config else {}
    del args.config, args.func

    for arg in vars(args):
        from_config = file_config.get(arg)
        from_environ = os.environ.get("NOISEKIT_{}")
        from_argv = getattr(args, arg)

        merged_config[arg] = from_config or from_environ or from_argv

    return merged_config


def soundfile_type(value):
    if not os.path.isfile(value):
        raise argparse.ArgumentTypeError(f"Sound file not found: {value}.")

    return {"path": value}


def soundtone_type(value):
    """
    Parse tone sounds parameters from args.

    value: 'square:90hz,10s,100%'
    returns: {'waveform': 'square', 'frequency': '90', 'amplitude': '100'}'
    """
    abbr_map = {"hz": "frequency", "%": "amplitude", "s": "duration"}
    tone_form, generator_raw_params = value.lower().split(":", 1)

    parameters = {"waveform": tone_form}

    for param in generator_raw_params.split(","):
        match = re.match(r"(\d+)(\D+)$", param)

        if not match:
            raise argparse.ArgumentTypeError(f"invalid tone parameter, format: '{generator_raw_params}'.")

        param_name, param_value = abbr_map[match.group(2)], int(match.group(1))

        if param_name == "amplitude":
            param_value = param_value / 100

        parameters[param_name] = param_value

    return parameters


def int_range(min_val, max_val):
    def validator(value):
        value = int(value)
        if value < min_val:
            raise argparse.ArgumentTypeError(f"value is below the min ({value} < {min_val})")
        elif value > max_val:
            raise argparse.ArgumentTypeError(f"value is above the max ({value} > {min_val})")

        return value

    return validator

#def valid_int_range(value):
#    start, end = value.split("-", 1)
#    return int(start), int(end)

def amplitude_as_percentage(raw_args):
    value = int(raw_args)
    if value > 100:
        raise argparse.ArgumentTypeError("maximum percentage is 100.")
    elif value < 0:
        raise argparse.ArgumentTypeError("minimum percentage is 0.")

    return value / 100


def register_audio_input_args(subparser):
    subparser.add_argument("-f", "--frames-per-buffer", default=1024, type=int)
    subparser.add_argument("-r", "--rate", default=44100, type=int)
#    subparser.add_argument("--channels", default=1, type=int_range(0, 1))  # useful to record stereo?
    subparser.add_argument("--format", dest="sample_format", default="Int16", choices=["Float32", "Int32", "Int24", "Int16", "UInt8"], help="PyAudio format type")
    subparser.add_argument("-no", "--no-overflow", action="store_true", default=False)


def register_generate(subparser):

    def run(args):
        from .audio.sound import SoundTone
        SoundTone(fd=args.output, amplitude=args.amplitude, duration=args.duration, frequency=args.frequency, rate=args.rate, waveform=args.waveform)
        args.output.close()

    subparser.set_defaults(func=run)
    subparser.add_argument("--amplitude", default=75, type=amplitude_as_percentage, metavar="[0-100]", help="amplitude as a percentage")
    subparser.add_argument("--duration", default=3, type=int, help="duration in seconds")
    subparser.add_argument("--frequency", default="90", help="frequency in hertz")
    subparser.add_argument("--rate", default=44100, type=int, help="frame rate")
    subparser.add_argument("--waveform", default="sine", choices=WAVE_GENERATORS.keys())
    subparser.add_argument("output", type=argparse.FileType('wb'), help="destination file")


def register_visualize(subparser):

    def run(args):
        from .visualize import Visualizer
        service = Service(Visualizer, load_settings(args))
        service.run()

    subparser.set_defaults(func=run)
    register_audio_input_args(subparser)
    subparser.add_argument("-s", "--sensitivity", default=1, type=int, help="amplitude sensitivity multiplier")

    subparser.add_argument("-R", "--record", type=argparse.FileType("wb"))

    subparser.add_argument("-as", "--amplitude-symbol", default="=")
    subparser.add_argument("-fs", "--frequency-symbol", default="-")
    subparser.add_argument("-ps", "--peak-symbol", default="|")

    subparser.add_argument("-low", "--low", dest="low_threshold", default=100, type=int, help="low level amplitude threshold in RMS")
    subparser.add_argument("-med", "--medium", dest="medium_threshold", default=200, type=int, help="medium level amplitude threshold in RMS")
    subparser.add_argument("-high", "--high", dest="high_threshold", default=300, type=int, help="high level amplitude threshold in RMS")

    subparser.add_argument("-qc", "--quiet-color")
    subparser.add_argument("-lc", "--low-color", default="blue")
    subparser.add_argument("-mc", "--medium-color", default="yellow")
    subparser.add_argument("-hc", "--high-color", default="red")


def register_mitigate(subparser):

    def run(args):
        from .mitigate import Mitigator
        service = Service(Mitigator, load_settings(args))
        service.run()

    DEFAULT_PLAYER = "aplay"

    if platform.system() == "Darwin":
        DEFAULT_PLAYER = "/Applications/VLC.app/Contents/MacOS/VLC --play-and-exit -"

    subparser.set_defaults(func=run)
    register_audio_input_args(subparser)

    subparser.add_argument("-R", "--record", type=argparse.FileType("wb"))
    subparser.add_argument("-q", "--quiet", action="store_true", default=False)

    subparser.add_argument("-P", "--psycho-mode", action="store_true", default=False, help="Enable analysis when the responses are played. So the mitigator will mitigate itself indefinitely.")
    subparser.add_argument("-p", "--picking-mode", default="random", choices=["cycle", "random"], help="Define how a specific sound are picked when a level is reached.")

    subparser.add_argument("--player", default=DEFAULT_PLAYER, help="Path to the player executable. Sounds paths are passed as an argument.")

    subparser.add_argument("-be", "--beat-every", type=int, help="Play the '--beat-sound' at a fixed interval. 0 on default, which disable the beat.")
    subparser.add_argument("-rl", "--reply-latency", default=0, type=int, help="seconds to wait before playing a triggered reply sound.")
    subparser.add_argument("--reply-window", type=int, help="minimum interval between two replies, in seconds.")
#    subparser.add_argument("--quiet-hours", default=None, type=valid_int_range, help="quiet hours in which no replies will be triggered.")

#    beat_every = subparser.add_mutually_exclusive_group()
#    beat_every.add_argument("-be", "--beat-every", type=int, default=0, help="Play the '--beat-sound' at a fixed interval. 0 on default, which disable the beat.")
#    beat_every.add_argument("-bb", "--beat-between", type=valid_int_range, default=None, help="Play the '--beat-sound' at a random interval range, eg '--beat-between 3-9'")
#    beat_every.add_argument("--beat-between", type=valid_int_range, default=(config.BEAT_MIN, config.BEAT_MAX), help="Play the '--beat-sound' at a random interval range, eg '--beat-between 3-9'")
#    beat_every.add_argument("--beat-random", action="store_true", default=False, help="Play the '--beat-sound' at a random interval between '--beat-min' and '--beat-max' ")
#    subparser.add_argument("--beat-min", default=config.BEAT_MIN, type=type(config.BEAT_MIN), help="Minimum interval for '--beat-random'.")
#    subparser.add_argument("--beat-max", default=config.BEAT_MAX, type=type(config.BEAT_MAX), help="Maximum interval for '--beat-random'.")

    beat_sound = subparser.add_mutually_exclusive_group()
    beat_sound.add_argument("-bs", "--beat-sound", dest="beat_soundfile", help="Sound file to play.", type=soundfile_type)
    beat_sound.add_argument("-bf", "--beat-frequency", dest="beat_soundtone", default="sine:1000hz,25%,1s", help="Frequency to sine.", type=soundtone_type)

    subparser.add_argument("-low", "--low", dest="low_threshold", default=100, type=int, help="Low level amplitude threshold in RMS")
    respond_low_with = subparser.add_mutually_exclusive_group()
    respond_low_with.add_argument("-ls", "--low-sound", dest="low_soundfiles", nargs="*", default=[], help="Add a sound file to play when low level threshold is raised.")
    respond_low_with.add_argument("-lt", "--low-frequency", dest="low_soundtones", nargs="*", default=[soundtone_type("sine:150hz,5s,25%")], help="Frequency to sine when no sound are specified for the level.", type=soundtone_type)

    subparser.add_argument("-med", "--medium", dest="medium_threshold", default=200, type=int, help="Medium level amplitude threshold in RMS")
    respond_medium_with = subparser.add_mutually_exclusive_group()
    respond_medium_with.add_argument("-ms", "--medium-sound", dest="medium_soundfiles", nargs="*", default=[], help="Add a sound file to play when medium level threshold is raised.")
    respond_medium_with.add_argument("-mt", "--medium-frequency", dest="medium_soundtones", nargs="*", default=[soundtone_type("damped:500hz,5s,50%")], help="Frequency to sine when no sound are specified for the level.", type=soundtone_type)

    subparser.add_argument("-high", "--high", dest="high_threshold", default=300, type=int, help="High level amplitude threshold in RMS")
    respond_high_with = subparser.add_mutually_exclusive_group()
    respond_high_with.add_argument("-hs", "--high-sound", nargs="*", dest="high_soundfiles", default=[], help="Add a sound file to play when high level threshold is raised.")
    respond_high_with.add_argument("-ht", "--high-frequency", dest="high_soundtones", nargs="*", default=[soundtone_type("square:15hz,5s,75%")], help="Frequency to sine when no sound are specified for the level.", type=soundtone_type)


def parse_args():

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description=__DESCRIPTION__
    )
    subparsers = parser.add_subparsers(dest="command", help="commands")
    register_generate(subparsers.add_parser("generate"))
    register_mitigate(subparsers.add_parser("mitigate"))
    register_visualize(subparsers.add_parser("visualize"))

    parser.add_argument("-c", "--config", type=argparse.FileType("rb"), help="config file path")
    parser.add_argument("-debug", "--debug", action="store_true", help="debugging mode")
    parser.add_argument("-log", "--loglevel", choices=["debug", "info", "warning", "error", "critical"], default="info")
    parser.add_argument("-v", "--version", action="version", version="%(prog)s {}".format(__VERSION__))
    return parser, parser.parse_args()


def main():
    parser, args = parse_args()
    if not args.command:
        parser.print_help()
        return

    del args.command

    setup_logging("debug" if args.debug else args.loglevel.upper())

    try:
        args.func(args)

    except Exception:
        logging.exception("noisekit ended abruptly.")
        return 127

if __name__ == "__main__":

    exit(main())
