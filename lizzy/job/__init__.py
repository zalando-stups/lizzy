"""
Copyright 2015 Zalando SE

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the
License. You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific
 language governing permissions and limitations under the License.
"""

import collections
import logging
import time
from threading import Thread

import rod

import lizzy.configuration as configuration
from lizzy.apps.senza import Senza
from lizzy.apps.common import ExecutionError
from lizzy.job.deployer import Deployer
from lizzy.models.stack import Stack

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
    all_stacks = Stack.all()  # Lizzy Stacks

    senza = Senza(region)
    try:
        senza_list = senza.list()  # All stacks in senza
    except ExecutionError:
        logger.exception("Couldn't get CF stacks. Exiting Job.")
        return False

    lizzy_stacks = collections.defaultdict(dict)  # stacks managed by lizzy as they are on Redis
    cf_stacks = collections.defaultdict(dict)  # stacks as they are on CloudFormation
    for cf_stack in senza_list:
        stack_name = '{stack_name}-{version}'.format_map(cf_stack)
        try:
            lizzy_stack = Stack.get(stack_name)
            logger.debug("Stack found.", extra={'lizzy.stack.id': stack_name})
            lizzy_stacks[lizzy_stack.stack_name][lizzy_stack.stack_version] = lizzy_stack
            cf_stacks[lizzy_stack.stack_name][lizzy_stack.stack_version] = cf_stack
        except KeyError:
            # Stack no handled by lizzy
            pass

    for lizzy_stack in all_stacks:
        if lizzy_stack.status in ['LIZZY:REMOVED', 'LIZZY:ERROR']:
            # There is nothing to do this, the stack is no more, it has expired, it's an ex-stack
            continue

        if lizzy_stack.lock(3600000):
            controller = Deployer(region, lizzy_stacks, cf_stacks, lizzy_stack)
            try:
                new_status = controller.handle()
                lizzy_stack.status = new_status
                lizzy_stack.save()
            finally:
                lizzy_stack.unlock()


def main_loop():  # pragma: no cover
    if uwsgi:
        uwsgi.signal_wait()
    config = configuration.Configuration()
    print(config.job_interval)
    logger.info('Connecting to Redis in job',
                extra={'redis_host': config.redis_host, 'redis_port': config.redis_port})  # TODO include uswgi info
    rod.connection.setup(redis_host=config.redis_host, port=config.redis_port)
    while True:
        t = Thread(target=check_status, args=(config.region,))
        t.daemon = True
        t.start()
        logger.debug('Waiting %d seconds to run the job again.', config.job_interval)
        time.sleep(config.job_interval)


if __name__ == '__main__':  # pragma: no cover
    main_loop()
