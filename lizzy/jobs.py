"""
Copyright 2015 Zalando SE

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the
License. You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific
 language governing permissions and limitations under the License.
"""

import logging

from lizzy.models.deployment import Deployment
import lizzy.senza_wrapper as senza

logger = logging.getLogger('lizzy.job')


def check_status():
    all_deployments = Deployment.all()
    logger.debug('In Job')
    stacks = senza.Senza.list()
    for stack in stacks:
        deployment_name = '{stack_name}-{version}'.format_map(stack)
        try:
            deployment = Deployment.get(deployment_name)
            logger.debug("'%s' not in redis.", deployment_name)
            logger.debug("'%s' found.", deployment.stack_name)
        except KeyError:
            logger.debug("'%s' not in redis.", deployment_name)

    for deployment in all_deployments:
        if deployment.lock(5000):
            logger.debug('ID: %s, STATUS: %s', deployment.deployment_id, deployment.status)
        else:
            logger.debug('Deployment object was locked skipping')
