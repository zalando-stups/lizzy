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
from lizzy import senza_wrapper as senza
from lizzy.models.stack import Stack


_failed_to_get_domains = object()  # sentinel value for when we failed to get domains from senza


class Deployer():

    logger = logging.getLogger('lizzy.job.deployer')

    def __init__(self, stacks: dict, stack: Stack):
        self.stacks = stacks
        self.stack = stack

    def _get_stack_status(self) -> str:
        """
        Get Stack Status in CloudFormation
        """
        try:
            cf_status = self.stacks[self.stack.stack_name][self.stack.stack_version]['status']
        except KeyError:
            cf_status = None
        return cf_status

    def default(self) -> str:
        """
        Handler for all other deployment status

        It replaces the status with the one from Cloud Formation or marks the deployment as removed if it no
        longer exists.
        """
        self.logger.debug("Trying to find the status of '%s' in AWS CF.", self.stack.stack_id)
        cloud_formation_status = self._get_stack_status()
        if cloud_formation_status is not None:
            self.logger.debug("'%s' status is '%s'", self.stack.stack_id, cloud_formation_status)
            new_status = 'CF:{}'.format(cloud_formation_status)
        else:
            # If this happens is because the stack was removed from aws
            self.logger.info("'%s' no longer exists, marking as removed", self.stack.stack_id)
            new_status = 'LIZZY:REMOVED'
        return new_status

    def deploying(self) -> str:
        """
        Handler for when deployment status=='LIZZY:DEPLOYING'

        Checks if the stack status changed.
        """
        cloud_formation_status = self._get_stack_status()

        if cloud_formation_status is None:  # Stack no longer exist.
            self.logger.info("'%s' no longer exists, marking as removed.", self.stack.stack_id)
            new_status = 'LIZZY:REMOVED'
        elif cloud_formation_status == 'CREATE_IN_PROGRESS':
            self.logger.debug("'%s' is still deploying.", self.stack.stack_id)
            new_status = 'LIZZY:DEPLOYING'
        elif cloud_formation_status == 'CREATE_COMPLETE':
            self.logger.info("'%s' stack created.", self.stack.stack_id)
            new_status = 'LIZZY:DEPLOYED'
        else:
            self.logger.info("'%s' status is '%s'.", self.stack.stack_id, cloud_formation_status)
            new_status = 'CF:{}'.format(cloud_formation_status)

        return new_status

    def deployed(self):
        """
        Handler for when deployment status=='LIZZY:DEPLOYED'

        Removes old versions and switches the traffic.
        """

        cloud_formation_status = self._get_stack_status()
        if cloud_formation_status is None:  # Stack no longer exist.
            self.logger.info("'%s' no longer exists, marking as removed", self.stack.stack_id)
            return 'LIZZY:REMOVED'

        all_versions = sorted(self.stacks[self.stack.stack_name].keys())
        self.logger.debug("Existing versions: %s", all_versions)
        # we want to keep only two versions
        number_of_versions_to_keep = self.stack.keep_stacks + 1  # keep provided old stacks + 1
        versions_to_remove = all_versions[:-number_of_versions_to_keep]
        self.logger.debug("Versions to be removed: %s", versions_to_remove)
        for version in versions_to_remove:
            self.logger.info("Removing '%s-%d'...", self.stack.stack_name, version)
            try:
                senza.Senza.remove(self.stack.stack_name, version)
                self.logger.info("'%s-%d' removed.", self.stack.stack_name, version)
            except Exception:
                self.logger.exception("Failed to remove '%s-%d'.", self.stack.stack_name, version)

        # Switch all traffic to new version
        try:
            domains = senza.Senza.domains(self.stack.stack_name)
        except senza.ExecutionError:
            self.logger.exception("Failed to get '%s' domains. Traffic will no be switched.",
                                  self.stack.stack_name)
            domains = _failed_to_get_domains

        if not domains:
            self.logger.info("'%s' doesn't have a domain so traffic will not be switched.", self.stack.stack_name)
        elif domains is not _failed_to_get_domains:
            self.logger.info("Switching '%s' traffic to '%s'.",
                             self.stack.stack_name, self.stack.stack_id)
            try:
                senza.Senza.traffic(stack_name=self.stack.stack_name,
                                    stack_version=self.stack.stack_version,
                                    percentage=self.stack.new_trafic)
            except senza.ExecutionError:
                self.logger.exception("Failed to switch '%s' traffic.", self.stack.stack_name)

        return 'CF:{}'.format(cloud_formation_status)

    def handle(self) -> str:
        """
        Does the right step for deployment status
        """
        if self.stack.status == 'LIZZY:NEW':
            return self.new()
        elif self.stack.status == 'LIZZY:DEPLOYING':
            return self.deploying()
        elif self.stack.status == 'LIZZY:DEPLOYED':
            return self.deployed()
        elif self.stack.status == 'LIZZY:ERROR':
            return 'LIZZY:ERROR'  # This is hardcoded because there is nothing more that can be done about it
        else:
            return self.default()

    def new(self) -> str:
        """
        Handler for when deployment status=='LIZZY:NEW'
        By default the stack is created
        """
        self.logger.info("Creating stack for '%s'...", self.stack.stack_id)
        if senza.Senza.create(self.stack.senza_yaml, self.stack.stack_version, self.stack.image_version):
            self.logger.info("Stack for '%s' created.", self.stack.stack_id)
            new_status = 'LIZZY:DEPLOYING'
        else:
            self.logger.error("Error creating stack for '%s'.", self.stack.stack_id)
            new_status = 'LIZZY:ERROR'

        return new_status
