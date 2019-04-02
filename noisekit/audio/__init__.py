import threading
from ..logging import get_logger


class BaseThread(threading.Thread):

    def __init__(self):
        super().__init__()
        self.shutdown_flag = threading.Event()
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")
