import threading
from ..logging import get_logger


class BaseThread(threading.Thread):
    """A thread is spawned by the `Service`, who pass his settings and thread-safe cache"""
    def __init__(self, service, settings):
        super().__init__()
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")
        self.service = service
        self.settings = settings
        self.shutdown_flag = threading.Event()
