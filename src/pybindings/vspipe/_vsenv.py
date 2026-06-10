import logging
import sys
import warnings

import vapoursynth as vs


class VSPipeFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        if record.levelno <= logging.DEBUG:
            prefix = "Debug"
        elif record.levelno <= logging.INFO:
            prefix = "Information"
        elif record.levelno <= logging.WARNING:
            prefix = "Warning"
        elif record.levelno <= logging.ERROR:
            prefix = "Critical"
        else:
            prefix = "Fatal"

        return f"{prefix}: {record.getMessage()}"


class CustomPolicy(vs.EnvironmentPolicy):
    def __init__(self, flags: int) -> None:
        self.flags = flags

    def on_policy_registered(self, special_api: vs.EnvironmentPolicyAPI) -> None:
        logging.captureWarnings(True)
        warnings.filterwarnings("always", module="__vapoursynth__")
        warnings.filterwarnings("always", module="vapoursynth")

        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(VSPipeFormatter())
        logging.root.handlers.clear()
        logging.root.addHandler(handler)
        logging.root.setLevel(logging.NOTSET)

        self._api = special_api
        logger = logging.getLogger("vapoursynth")

        self._data = self._api.create_environment(self.flags)
        self._api.set_logger(
            self._data,
            lambda level, msg: logger.log(vs.LOG_LEVEL_MAP[vs.MessageType(level)], msg),
        )

    def on_policy_cleared(self) -> None:
        self._api.destroy_environment(self._data)
        logging.captureWarnings(False)
        warnings.resetwarnings()

        logging.root.handlers.clear()
        logging.basicConfig(level=logging.WARN, format="%(message)s")

        del self._data
        del self._api

    def get_current_environment(self) -> vs.EnvironmentData:
        return self._data

    def set_environment(self, environment: vs.EnvironmentData | None) -> vs.EnvironmentData:
        return self._data
