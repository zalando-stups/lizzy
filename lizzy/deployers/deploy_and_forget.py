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

from lizzy.deployers.base import BaseDeployer
import lizzy.senza_wrapper as senza


class DeployAndForget(BaseDeployer):

    """
    Just deploy the stack
    """

    logger = logging.getLogger('lizzy.controller.deployment.deploy_and_forget')

    def new(self) -> str:
        """
        Handler for when deployment status=='LIZZY:NEW'
        """
        self.logger.debug("Creating stack for '%s'...", self.deployment.deployment_id)
        if senza.Senza.create(self.deployment.senza_yaml, self.deployment.stack_version, self.deployment.image_version):
            self.logger.debug("Stack for '%s' created.", self.deployment.deployment_id)
            # With this strategy the deployment is done as soon as we create the stack
            new_status = 'LIZZY:DEPLOYED'
        else:
            self.logger.error("Error creating stack for '%s'.", self.deployment.deployment_id)
            new_status = 'LIZZY:ERROR'

        return new_status
