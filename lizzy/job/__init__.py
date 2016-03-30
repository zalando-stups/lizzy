from typing import List  # NOQA
import collections
import logging
import time
from threading import Thread

import rod

import lizzy.configuration as configuration
from lizzy.apps.senza import Senza
from lizzy.apps.common import ExecutionError
from lizzy.job.deployer import Deployer
from lizzy.models.stack import Stack, REMOVED_STACK
from lizzy.exceptions import ObjectNotFound

try:
    # From http://uwsgi-docs.readthedocs.org/en/latest/PythonModule.html
    # "The uWSGI server automagically adds a uwsgi module into your Python apps."
    # This means the module doesn't exist during testing
    import uwsgi
except ImportError:
    uwsgi = None

logger = logging.getLogger('lizzy.job')


def check_status(region: str):
    logger.debug('In Job')
    all_stacks = Stack.all()  # type: List[Stack]

    senza = Senza(region)
    try:
        senza_list = senza.list()  # All stacks in senza
    except ExecutionError:
        logger.exception("Couldn't get CF stacks. Exiting Job.")
        return False

    logger.debug('Got %d senza stacks.', len(senza_list),
                 extra={'senza_stacks': senza_list})

    lizzy_stacks = collections.defaultdict(dict)  # stacks managed by lizzy as they are on Redis
    cf_stacks = collections.defaultdict(dict)  # stacks as they are on CloudFormation
    for cf_stack in senza_list:
        stack_name = '{stack_name}-{version}'.format_map(cf_stack)
        try:
            lizzy_stack = Stack.get(stack_name)
            logger.debug("Stack found in Redis.",
                         extra={'lizzy.stack.id': stack_name})
            lizzy_stacks[lizzy_stack.stack_name][lizzy_stack.stack_version] = lizzy_stack
            cf_stacks[lizzy_stack.stack_name][lizzy_stack.stack_version] = cf_stack
        except ObjectNotFound:
            # Stack no handled by lizzy
            logger.debug("Stack not found in Redis.",
                         extra={'lizzy.stack.id': stack_name})

    for lizzy_stack in all_stacks:
        if lizzy_stack.status in ['LIZZY:REMOVED', 'LIZZY:ERROR']:
            # Delete broken and removed stacks as it makes no sense to keep
            # them around
            # TODO remove this in a later version (2.0???)
            logger.info('Deleting stack from Redis.',
                        extra={'lizzy.stack.id': lizzy_stack.stack_id})
            lizzy_stack.delete()
            continue

        if lizzy_stack.lock(3600000):
            controller = Deployer(region, lizzy_stacks, cf_stacks, lizzy_stack)
            try:
                new_status = controller.handle()
                if new_status is not REMOVED_STACK:
                    lizzy_stack.status = new_status
                    lizzy_stack.save()
                else:
                    # stack no longer exists
                    logger.info('Deleting stack from Redis.',
                                extra={'lizzy.stack.id': lizzy_stack.stack_id})
                    lizzy_stack.delete()
            finally:
                lizzy_stack.unlock()


def main_loop():  # pragma: no cover
    if uwsgi:
        uwsgi.signal_wait()
    config = configuration.Configuration()
    print(config.job_interval)
    logger.info('Connecting to Redis in job',
                extra={'redis_host': config.redis_host,
                       'redis_port': config.redis_port})
    rod.connection.setup(redis_host=config.redis_host, port=config.redis_port)
    while True:
        t = Thread(target=check_status, args=(config.region,))
        t.daemon = True
        t.start()
        logger.debug('Waiting %d seconds to run the job again.',
                     config.job_interval)
        time.sleep(config.job_interval)


if __name__ == '__main__':  # pragma: no cover
    main_loop()
