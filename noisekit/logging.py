import os
import logging


class Message(object):

    def __init__(self, fmt, args, kwargs):
        self.fmt = fmt
        self.args = args
        self.kwargs = kwargs

    def __str__(self):
        return self.fmt.format(*self.args, **self.kwargs)


class FormatAdapter(logging.LoggerAdapter):

    def __init__(self, logger, extra=None):
        super(FormatAdapter, self).__init__(logger, extra or {})

    def log(self, level, msg, *args, **kwargs):
        if self.isEnabledFor(level):
            msg, kwargs = self.process(msg, kwargs)
            self.logger.log(level, Message(msg, args, kwargs))


def get_logger(name):
    return logging.getLogger(name)
#    return FormatAdapter(logging.getLogger(name))


def setup_logging(level):
    logger = logging.getLogger()
    logger.setLevel(level)
    handler = logging.StreamHandler()
    line_template = "[{levelname}] ~ {message}"

    # in runned by systemd, there is no reason to display datetime to syslog
    if os.getppid() != 1:
        line_template = "{asctime:15} " + line_template

    formatter = logging.Formatter(line_template, datefmt="%Y-%m-%d %H:%M:%S", style="{")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
