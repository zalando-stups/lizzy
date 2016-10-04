from raven import Client

from .configuration import Configuration
from .logging import init_logging
from .version import VERSION

__all__ = ['config', 'logger', 'sentry_client']

config = Configuration()  # pylint: disable=invalid-name
logger = init_logging(config.log_format, config.log_level)  # pylint: disable=invalid-name

sentry_client = Client(config.sentry_dsn,
                       release=VERSION)
