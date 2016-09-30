import datetime
import logging
import os

from lizzy import config
from metricz import MetricWriter

server = None
logger = logging.getLogger('lizzy.metrics')  # pylint: disable=invalid-name


def push(key, value):
    if config.kairosdb_url:
        global server
        if not server:
            server = MetricWriter(kairosdb_url=config.kairosdb_url,
                                  fail_silently=True,
                                  timeout=4)
        try:
            server.write_metric(
                '{}.lizzy.{}'.format(config.metrics_prefix, key),
                value,
                tags={
                    'app': 'lizzy',
                    'version': os.environ.get("APPLICATION_VERSION", "")
                })
        except IOError as ex:
            logger.error('Error to push metric {}: {}'.format(key, str(ex)))


def count(key):
    push(key, 1)


class MeasureRunningTime:
    def __init__(self, key):
        self.key = key
        self.start_time = datetime.datetime.now()

    def finish(self):
        end_time = datetime.datetime.now()
        running_time = int((end_time - self.start_time).total_seconds())
        push(self.key, running_time)
