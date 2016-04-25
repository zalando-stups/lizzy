import logging

from lizzy.apps.common import ExecutionError
from lizzy.apps.senza import Senza
from lizzy.models.stack import REMOVED_STACK, Stack

# sentinel value for when we failed to get domains from senza
FAILED_TO_GET_DOMAINS = object()


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
