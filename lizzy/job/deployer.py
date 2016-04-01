import logging

from lizzy.apps.common import ExecutionError
from lizzy.apps.senza import Senza
from lizzy.models.stack import Stack, REMOVED_STACK

_failed_to_get_domains = object()  # sentinel value for when we failed to get domains from senza


class Deployer:
    logger = logging.getLogger('lizzy.job.deployer')

    def __init__(self,
                 region: str,
                 lizzy_stacks: dict,
                 cf_stacks: dict,
                 stack: Stack):
        self.senza = Senza(region)
        self.lizzy_stacks = lizzy_stacks  # All stacks in lizzy
        self.cf_stacks = cf_stacks  # Stacks on CloudFormation
        self.stack = stack  # Stack to deploy

    @property
    def log_info(self) -> dict:
        log_info = dict()
        log_info['lizzy.stack.name'] = self.stack.stack_name
        log_info['lizzy.stack.id'] = self.stack.stack_id
        log_info['lizzy.stack.traffic'] = self.stack.traffic

        cloud_formation_status = self._get_stack_status()
        if cloud_formation_status:
            log_info['cf_status'] = cloud_formation_status

        return log_info

    def _get_stack_status(self) -> str:
        """
        Get Stack Status in CloudFormation
        """
        try:
            cf_status = self.cf_stacks[self.stack.stack_name][self.stack.stack_version]['status']
        except KeyError:
            cf_status = None
        return cf_status

    def default(self) -> str:
        """
        Handler for all other deployment status

        It replaces the status with the one from Cloud Formation or marks the
        deployment as removed if it no
        longer exists.
        """

        self.logger.debug("Updating stack status based on AWS CF.",
                          extra=self.log_info)
        cloud_formation_status = self._get_stack_status()
        if cloud_formation_status is not None:
            self.logger.debug("Stack status updated", extra=self.log_info)
            new_status = 'CF:{}'.format(cloud_formation_status)
            return new_status
        else:
            # If this happens is because the stack was removed from aws
            self.logger.info("Stack no longer exists, marking as removed",
                             extra=self.log_info)
            return REMOVED_STACK

    def deploying(self) -> str:
        """
        Handler for when deployment status=='CF:CREATE_IN_PROGRESS'

        Checks if the stack status changed.
        """
        cloud_formation_status = self._get_stack_status()

        if cloud_formation_status is None:  # Stack no longer exist.
            self.logger.info("Stack no longer exists, marking as removed.",
                             extra=self.log_info)
            return REMOVED_STACK

        if cloud_formation_status == 'CREATE_COMPLETE':
            self.logger.info("Stack created.", extra=self.log_info)
            new_status = 'LIZZY:DEPLOYED'
        elif cloud_formation_status == 'CREATE_IN_PROGRESS':
            # Stack is still deploying
            # While this condition is mostly equivalent to the else it is
            # special enough to log differently
            self.logger.debug("Stack is still deploying.", extra=self.log_info)
            new_status = 'CF:CREATE_IN_PROGRESS'
        else:
            self.logger.info("Updating stack status based on AWS CF.",
                             extra=self.log_info)
            new_status = 'CF:{}'.format(cloud_formation_status)

        return new_status

    def deployed(self):
        """
        Handler for when deployment status=='LIZZY:DEPLOYED'

        Removes old versions and switches the traffic.
        """

        cloud_formation_status = self._get_stack_status()
        if cloud_formation_status is None:  # Stack no longer exist.
            self.logger.info("Stack no longer exists, marking as removed",
                             extra=self.log_info)
            return REMOVED_STACK

        # Switch all traffic to new version
        try:
            domains = self.senza.domains(self.stack.stack_name)
        except ExecutionError:
            self.logger.exception("Failed to get domains. Traffic will no be switched.",
                                  extra=self.log_info)
            domains = _failed_to_get_domains

        if not domains:
            self.logger.info("App doesn't have a domain so traffic will not be switched.",
                             extra=self.log_info)
        elif domains is not _failed_to_get_domains and self.stack.traffic > 0:
            # if new stack's traffic is zero the traffic does not need to be
            # switched. More details at: https://github.com/zalando/lizzy/issues/83
            self.logger.info("Switching app traffic.", extra=self.log_info)
            try:
                self.senza.traffic(stack_name=self.stack.stack_name,
                                   stack_version=self.stack.stack_version,
                                   percentage=self.stack.traffic)
            except ExecutionError:
                self.logger.exception("Failed to switch app traffic.",
                                      extra=self.log_info)

        all_versions = sorted(
            self.lizzy_stacks[self.stack.stack_name].values(),
            key=lambda s: s.creation_time)
        all_versions_names = [stack.stack_name for stack in all_versions]

        self.logger.debug("Existing versions: %s", all_versions_names,
                          extra=self.log_info)
        # we want to keep only two versions
        number_of_versions_to_keep = self.stack.keep_stacks + 1  # keep provided old stacks + 1
        versions_to_remove = all_versions_names[:-number_of_versions_to_keep]
        self.logger.debug("Versions to be removed: %s", versions_to_remove,
                          extra=self.log_info)
        for version in versions_to_remove:
            stack_id = '{}-{}'.format(self.stack.stack_name, version)
            log_info = {'lizzy.stack.id': stack_id, 'lizzy.new_stack.id':
                        self.stack.stack_id}
            self.logger.info("Removing stack...", extra=log_info)
            try:
                self.senza.remove(self.stack.stack_name, version)
                self.logger.info("Stack removed.", extra=log_info)
            except Exception:
                self.logger.exception("Failed to remove stack.",
                                      extra=log_info)

        return 'CF:{}'.format(cloud_formation_status)

    def handle(self) -> str:
        """
        Does the right step for deployment status.
        """
        # TODO remove LIZZY:DEPLOYING in a future version (1.9?)
        action_by_status = {
            'LIZZY:DEPLOYING': self.deploying,
            'CF:CREATE_IN_PROGRESS': self.deploying,
            'LIZZY:DEPLOYED': self.deployed,
        }
        handler = action_by_status.get(self.stack.status, self.default)
        return handler()
