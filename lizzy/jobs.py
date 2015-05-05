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

from lizzy.models.deployment import Deployment
import lizzy.senza_wrapper as senza

logger = logging.getLogger('lizzy.job')


def deploy_and_forget(deployment):
    if senza.Senza.create(deployment.senza_yaml, deployment.stack_version, deployment.image_version):
        deployment.status = 'LIZZY_DEPLOYING'
    else:
        deployment.status = 'LIZZY_ERROR'


def deploy_blue_green(deployment):
    pass


def check_status():
    all_deployments = Deployment.all()
    logger.debug('In Job')
    stacks = senza.Senza.list()
    lizzy_stacks = collections.defaultdict(dict)  # stacks managed by lizzy
    for stack in stacks:
        deployment_name = '{stack_name}-{version}'.format_map(stack)
        try:
            deployment = Deployment.get(deployment_name)
            logger.debug("'%s' found.", stack)
            lizzy_stacks[deployment.stack_name][deployment.stack_version] = stack
        except KeyError:
            pass

    for deployment in all_deployments:
        if deployment.status == 'LIZZY_REMOVED':
            # There is nothing to do this, the stack is no more, it has expired, it's an ex-stack
            ...
        elif deployment.status == 'LIZZY_NEW' and deployment.lock(3600000):
            logger.debug("Trying to deploy '%s'", deployment.deployment_id)
            if deployment.strategy == 'BLUE_GREEN':
                deploy_blue_green(deployment)
            else:
                deploy_and_forget(deployment)
            deployment.save()
            deployment.unlock()
        elif deployment.lock(3600000):
            try:
                deployment.status = lizzy_stacks[deployment.stack_name][deployment.stack_version]['status']
            except KeyError:
                # If this happens is because the stack was removed from aws
                logger.debug("'%s' no longer exists, marking as removed", deployment.deployment_id)
                deployment.status = 'LIZZY_REMOVED'
            deployment.save()
            deployment.unlock()
            logger.debug('ID: %s, STATUS: %s', deployment.deployment_id, deployment.status)
        else:
            logger.debug('ID: %s, STATUS: %s', deployment.deployment_id, deployment.status)
