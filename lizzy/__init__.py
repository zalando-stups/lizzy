from .configuration import Configuration
from .logging import init_logging

config = Configuration()  # pylint: disable=invalid-name
logger = init_logging(config.log_format, config.log_level)  # pylint: disable=invalid-name
