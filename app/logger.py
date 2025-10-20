from logging import Logger, getLogger

LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": ("%(asctime)s %(levelname)s %(module)s.%(funcName)s(%(lineno)d) %(message)s"),
            "datefmt": "%Y-%m-%d %H:%M:%S",
        }
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
        }
    },
    "loggers": {
        "logger": {"handlers": ["default"], "level": "INFO", "propagate": False},
        "uvicorn.access": {"handlers": [], "level": "INFO", "propagate": False},
        "uvicorn.error": {"handlers": ["default"], "level": "INFO"},
    },
}


def get_logger(name: str = "logger") -> Logger:
    return getLogger(name=name)
