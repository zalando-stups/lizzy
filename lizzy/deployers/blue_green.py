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


class BlueGreenDeployer(BaseDeployer):

    logger = logging.getLogger('lizzy.controller.deployment.blue_green')

    def deploying(self) -> str:
        cloud_formation_status = self._get_stack_status()

        if cloud_formation_status is None:  # Stack no longer exist.
            new_status = 'LIZZY:REMOVED'
        elif cloud_formation_status == 'CREATE_COMPLETE':
            new_status = 'LIZZY:DEPLOYED'
        else:
            new_status = 'CF:{}'.format(cloud_formation_status)

        return new_status

    def deployed(self):
        cloud_formation_status = self._get_stack_status()
        if cloud_formation_status is None:  # Stack no longer exist.
            return 'LIZZY:REMOVED'

        all_versions = sorted(self.stacks[self.deployment.stack_name].keys())
        self.logger.debug("Existing versions: %s", all_versions)
        # we want to keep only two versions
        versions_to_remove = all_versions[:-2]
        self.logger.debug("Versions to be removed: %s", versions_to_remove)
        for version in versions_to_remove:
            self.logger.info("Removing '%s-%d'".format(self.deployment.stack_name, version))
            senza.Senza.remove(self.deployment.stack_name, version)

        # TODO Switch traffic

        return 'CF:{}'.format(cloud_formation_status)
