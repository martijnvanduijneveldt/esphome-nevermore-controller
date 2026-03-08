import logging

class NevermoreLogAdapter(logging.LoggerAdapter):
    def __init__(self, logger, prefix):
        super().__init__(logger)
        self._prefix = prefix

    def process(self, msg, kwargs):
        return f"[{self._prefix}] {msg}", kwargs