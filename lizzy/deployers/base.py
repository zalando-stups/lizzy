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


class BaseDeployer:

    logger = logging.getLogger('lizzy.controller.deployment.DeploymentController')

    def __init__(self, stacks: dict, deployment: Deployment):
        self.stacks = stacks
        self.deployment = deployment

    def _get_stack_status(self) -> str:
        """
        Get Stack Status in CloudFormation
        """
        try:
            cf_status = self.stacks[self.deployment.stack_name][self.deployment.stack_version]['status']
        except KeyError:
            cf_status = None
        return cf_status

    def handle(self) -> str:
        """
        Does the right step for deployment status
        """
        if self.deployment.status == 'LIZZY:NEW':
            return self.new()
        elif self.deployment.status == 'LIZZY:DEPLOYING':
            return self.deploying()
        elif self.deployment.status == 'LIZZY:DEPLOYED':
            return self.deployed()
        elif self.deployment.status == 'LIZZY:ERROR':
            return 'LIZZY:ERROR'  # This is hardcoded because there is nothing more that can be done about it
        else:
            return self.default()

    def new(self) -> str:
        """
        Handler for when deployment status=='LIZZY:NEW'
        By default the stack is created
        """
        self.logger.info("Creating stack for '%s'...", self.deployment.deployment_id)
        if senza.Senza.create(self.deployment.senza_yaml, self.deployment.stack_version, self.deployment.image_version):
            self.logger.info("Stack for '%s' created.", self.deployment.deployment_id)
            new_status = 'LIZZY:DEPLOYING'
        else:
            self.logger.error("Error creating stack for '%s'.", self.deployment.deployment_id)
            new_status = 'LIZZY:ERROR'

        return new_status

    def deploying(self) -> str:
        """
        Handler for when deployment status=='LIZZY:DEPLOYING'
        By default don't do anything
        """
        return self.deployment.status

    def deployed(self) -> str:
        """
        Handler for when deployment status=='LIZZY:DEPLOYED'
        By default don't do anything
        """
        return self.deployment.status

    def default(self) -> str:
        """
        Handler for all other deployment status
        By default it replaces the status with the one from Cloud Formation or marks the deployment as removed if it no
        longer exists.
        """
        self.logger.debug("Trying to find the status of '%s' in AWS CF.", self.deployment.deployment_id)
        cloud_formation_status = self._get_stack_status()
        if cloud_formation_status is not None:
            self.logger.debug("'%s' status is '%s'", self.deployment.deployment_id, cloud_formation_status)
            new_status = 'CF:{}'.format(cloud_formation_status)
        else:
            # If this happens is because the stack was removed from aws
            self.logger.info("'%s' no longer exists, marking as removed", self.deployment.deployment_id)
            new_status = 'LIZZY:REMOVED'
        return new_status
