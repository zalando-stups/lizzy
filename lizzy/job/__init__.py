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

from lizzy import senza_wrapper as senza
from lizzy.job.deployer import Deployer
from lizzy.models.stack import Stack

logger = logging.getLogger('lizzy.job')


def check_status():
    all_stacks = Stack.all()
    logger.debug('In Job')

    try:
        stacks = senza.Senza.list()
    except senza.ExecutionError:
        logger.exception("Couldn't get CF stacks. Exiting Job.")
        return

    lizzy_stacks = collections.defaultdict(dict)  # stacks managed by lizzy
    for stack in stacks:
        stack_name = '{stack_name}-{version}'.format_map(stack)
        try:
            stack = Stack.get(stack_name)
            logger.debug("'%s' found.", stack)
            lizzy_stacks[stack.stack_name][stack.stack_version] = stack
        except KeyError:
            pass

    for stack in all_stacks:
        if stack.status in ['LIZZY:REMOVED', 'LIZZY:ERROR']:
            # There is nothing to do this, the stack is no more, it has expired, it's an ex-stack
            continue

        if stack.lock(3600000):
            controller = Deployer(lizzy_stacks, stack)
            try:
                new_status = controller.handle()
                stack.status = new_status
                stack.save()
            finally:
                stack.unlock()
