from .configuration import Configuration
from .logging import init_logging

config = Configuration()
logger = init_logging(config.log_format, config.log_level)
