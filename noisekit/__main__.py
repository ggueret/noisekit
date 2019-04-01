"""
"""
from __future__ import absolute_import
import os
import sys
import json
import argparse
import logging

from .logging import setup_logging
from .service import Service
from . import config
from . import __DESCRIPTION__, __VERSION__


def load_settings(args):
    """Load settings using in order: envion > argv > config > default"""
    merged_config = {}
    file_config = json.load(args.config) if args.config else {}
    del args.config, args.func

    for arg in vars(args):
        default_value = getattr(config, arg.upper())

        from_environ = os.environ.get("NOISEKIT_{}")
        from_argv = getattr(args, arg) if getattr(args, arg) is not default_value else None
        from_config = file_config.get(arg)

        merged_config[arg] = from_environ or from_argv or from_config or default_value

    return merged_config


def valid_int_range(raw_args):
    minimum, maximum = raw_args.split("-", 1)
    return int(minimum), int(maximum)

#    raise argparse.ArgumentTypeError()
#    return map(int, raw_args.split("-", 1))


def amplitude_as_percentage(raw_args):
    value = int(raw_args)
    if value > 100:
        raise argparse.ArgumentTypeError("maximum percentage is 100.")
    elif value < 0:
        argparse.ArgumentTypeError("minimum percentage is 0.")

    return value / 100


def run(args):
    from . import NoisyBuddy
#    setup_logging(getattr(logging, args.log_level.upper()) if not args.visualize else logging.CRITICAL)
    knocked = NoisyBuddy(**load_settings(args))
    knocked.run()


def register_audio_input_args(subparser):
    # To capture low frequencies, requires a highter value, eg 10Hz was done in 0.1 seconds.
    subparser.add_argument("-f", "--frames-per-buffer", default=config.FRAMES_PER_BUFFER, type=type(config.FRAMES_PER_BUFFER))
    subparser.add_argument("-r", "--rate", default=config.RATE, type=type(config.RATE))
#    subparser.add_argument("--channels", default=config.CHANNELS, type=type(config.CHANNELS))
    subparser.add_argument("--format", default=config.FORMAT, choices=["Float32", "Int32", "Int24", "Int16", "UInt8"], help="PyAudio format type")
    subparser.add_argument("-no", "--no-overflow", action="store_true", default=False)


def register_generate(subparser):

    def run(args):
        from . import generate
        channels = ((generate.square_wave(args.frequency, 44100, args.amplitude),) for i in range(1))
        samples = generate.compute_samples(channels, 44100 * args.duration)
        generate.write_wavefile(args.output, samples, 44100 * args.duration, 2, 16 // 8, 44100)

    subparser.set_defaults(func=run)
    subparser.add_argument("--frequency", default="10", help="frequency in hertz")
    subparser.add_argument("--waveform", default="sine", choices=["sine", "square"])
    subparser.add_argument("--duration", default=1, type=int, help="duration in seconds")
    subparser.add_argument("--amplitude", default=50, type=amplitude_as_percentage, metavar="[0-100]", help="amplitude as a percentage")
    subparser.add_argument("--output", default="output.wav", help="output file")
#    subparser.add_argument("--output", type=argparse.FileType('w'), default=sys.stdout)


def register_visualize(subparser):

    def run(args):
        from .visualize import Visualizer
        visualizer = Visualizer(**vars(args))
        service = Service(visualizer)
        service.run()

    subparser.set_defaults(func=run)
    register_audio_input_args(subparser)
    subparser.add_argument("-s", "--sensitivity", default=config.SENSITIVITY, type=type(config.SENSITIVITY), help="amplitude sensitivity multiplier")

    subparser.add_argument("-R", "--record", type=argparse.FileType("wb"))

    subparser.add_argument("-as", "--amplitude-symbol", default=config.AMPLITUDE_SYMBOL)
    subparser.add_argument("-fs", "--frequency-symbol", default=config.FREQUENCY_SYMBOL)
    subparser.add_argument("-ps", "--peak-symbol", default=config.PEAK_SYMBOL)

    subparser.add_argument("-lt", "--low", dest="low_threshold", default=config.LOW_THRESHOLD, type=type(config.LOW_THRESHOLD), help="low level amplitude threshold in RMS")
    subparser.add_argument("-mt", "--medium", dest="medium_threshold", default=config.MEDIUM_THRESHOLD, type=type(config.LOW_THRESHOLD), help="medium level amplitude threshold in RMS")
    subparser.add_argument("-ht", "--high", dest="high_threshold", default=config.HIGH_THRESHOLD, type=type(config.LOW_THRESHOLD), help="high level amplitude threshold in RMS")

    subparser.add_argument("-qc", "--quiet-color", default=config.QUIET_COLOR)
    subparser.add_argument("-lc", "--low-color", default=config.LOW_COLOR)
    subparser.add_argument("-mc", "--medium-color", default=config.MEDIUM_COLOR)
    subparser.add_argument("-hc", "--high-color", default=config.HIGH_COLOR)


def register_mitigate(subparser):

    def run(args):
        from .mitigate import Mitigator
        mitigator = Mitigator(**load_settings(args))
        service = Service(mitigator)
        service.run()

    subparser.set_defaults(func=run)
    register_audio_input_args(subparser)
    subparser.add_argument("-c", "--config", type=argparse.FileType("rb"))

    subparser.add_argument("-R", "--record", type=argparse.FileType("wb"))
    subparser.add_argument("-q", "--quiet", action="store_true", default=False)

    subparser.add_argument("-P", "--psycho-mode", action="store_true", default=False, help="Enable analysis when the responses are played. So the mitigator will mitigate itself indefinitely.")
    subparser.add_argument("-p", "--picking-mode", default=config.PICKING_MODE, choices=["cycle", "random"], help="Define how a specific sound are picked when a level is reached.")

    subparser.add_argument("--player", default=config.PLAYER, help="Path to the player executable. Sounds paths are passed as an argument.")

    subparser.add_argument("-be", "--beat-every", type=int, default=60, help="Play the '--beat-sound' at a fixed interval. 0 on default, which disable the beat.")

#    beat_every = subparser.add_mutually_exclusive_group()
#    beat_every.add_argument("-be", "--beat-every", type=int, default=0, help="Play the '--beat-sound' at a fixed interval. 0 on default, which disable the beat.")
#    beat_every.add_argument("-bb", "--beat-between", type=valid_int_range, default=None, help="Play the '--beat-sound' at a random interval range, eg '--beat-between 3-9'")
#    beat_every.add_argument("--beat-between", type=valid_int_range, default=(config.BEAT_MIN, config.BEAT_MAX), help="Play the '--beat-sound' at a random interval range, eg '--beat-between 3-9'")
#    beat_every.add_argument("--beat-random", action="store_true", default=False, help="Play the '--beat-sound' at a random interval between '--beat-min' and '--beat-max' ")
#    subparser.add_argument("--beat-min", default=config.BEAT_MIN, type=type(config.BEAT_MIN), help="Minimum interval for '--beat-random'.")
#    subparser.add_argument("--beat-max", default=config.BEAT_MAX, type=type(config.BEAT_MAX), help="Maximum interval for '--beat-random'.")

    beat_with = subparser.add_mutually_exclusive_group()
    beat_with.add_argument("-bs", "--beat-sound", default=config.BEAT_SOUND, help="Sound file to play.")
    beat_with.add_argument("-bf", "--beat-frequency", default=config.BEAT_FREQUENCY, help="Frequency to sine.")

    subparser.add_argument("-lt", "--low", dest="low_threshold", default=config.LOW_THRESHOLD, type=type(config.LOW_THRESHOLD), help="Low level amplitude threshold in RMS")
    respond_low_with = subparser.add_mutually_exclusive_group()
    respond_low_with.add_argument("-ls", "--low-sound", dest="low_sounds", nargs="*", help="Add a sound to play when low level threshold is raised.")
    respond_low_with.add_argument("-lf", "--low-frequency", default=config.LOW_FREQUENCY, help="Frequency to sine when no sound are specified for the level.")

    subparser.add_argument("-mt", "--medium", dest="medium_threshold", default=config.MEDIUM_THRESHOLD, type=type(config.LOW_THRESHOLD), help="Medium level amplitude threshold in RMS")
    respond_medium_with = subparser.add_mutually_exclusive_group()
    respond_medium_with.add_argument("-ms", "--medium-sound", dest="medium_sounds", nargs="*", help="Add a sound to play when medium level threshold is raised.")
    respond_medium_with.add_argument("-mf", "--medium-frequency", default=config.MEDIUM_FREQUENCY, help="Frequency to sine when no sound are specified for the level.")

    subparser.add_argument("-ht", "--high", dest="high_threshold", default=config.HIGH_THRESHOLD, type=type(config.LOW_THRESHOLD), help="High level amplitude threshold in RMS")
    respond_high_with = subparser.add_mutually_exclusive_group()
    respond_high_with.add_argument("-hs", "--high-sound", nargs="*", dest="high_sounds", help="Add a sound to play when high level threshold is raised.")
    respond_high_with.add_argument("-hf", "--high-frequency", default=config.HIGH_FREQUENCY, help="Frequency to sine when no sound are specified for the level.")


def install(args):

    template = """[Service]
Type=simple
User={user}
Group={group}
ExecStart={binary} run --config=/root/noisekit.config.json

[Unit]
Description=knocked
After=syslog.target

[Install]
WantedBy=multi-user.target"""

    context = {}
    context["binary"] = sys.argv[0]
    context["user"], context["group"] = args.user, args.group

#    with open(os.path.join(BASEDIR_PATH, os.pardir, "noisekit.service"), "r") as f:
#        template = f.read()

    # check if systemd is used.
    with open("/etc/systemd/system/noisekit.service", "w") as f:
        f.write(template.format(**context))


def parse_args():

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description=__DESCRIPTION__
    )
    parser.add_argument("--version", action="version", version="%(prog)s {}".format(__name__))
    parser.add_argument("--loglevel", choices=["debug", "info", "warning", "error", "critical"], default="info")
    subparsers = parser.add_subparsers(dest="command", help="commands")

    register_generate(subparsers.add_parser("generate"))
    register_visualize(subparsers.add_parser("visualize"))
    register_mitigate(subparsers.add_parser("mitigate"))

    return parser.parse_args()


def main():
    args = parse_args()
    if not args.command:
        return
    setup_logging(getattr(logging, args.loglevel.upper()))
    logging.info("[~] starting %s module of noisekit v%s", args.command, __VERSION__)

    del args.command
    try:
        args.func(args)

    except Exception:
        logging.exception("noisekit exited abruptly:")
        raise

#    logging.info("noisekit exited properly.")

if __name__ == "__main__":

    main()
