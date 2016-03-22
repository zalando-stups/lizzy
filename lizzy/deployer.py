
from lizzy.apps.senza import Senza
from lizzy.models.stack import Stack
from lizzy.logging import logger
from lizzy.configuration import config
from lizzy.exceptions import (AMIImageNotUpdated, ExecutionError,
                              SenzaDomainsError, SenzaTrafficError,
                              TrafficNotUpdated, StackDeleteException)


class InstantDeployer:
    """Run senza commands """

    def __init__(self, stack: Stack):
        self.senza = Senza(config.region)
        self.stack = stack
        self.logger = logger(__name__)

    @property
    def log_info(self) -> dict:
        return {
            'lizzy.stack.id': self.stack.stack_id,
            'lizzy.stack.name': self.stack.stack_name
        }

    def change_traffic(self, new_traffic: int):
        try:
            domains = self.senza.domains(self.stack.stack_name)
            if domains:
                self.logger.info("Switching app traffic to stack.",
                                 extra=self.log_info)

                self.senza.traffic(stack_name=self.stack.stack_name,
                                   stack_version=self.stack.stack_version,
                                   percentage=new_traffic)
            else:
                self.logger.info("App does not have a domain so traffic will"
                                 " not be switched.", extra=self.log_info)
                raise TrafficNotUpdated("App does not have a domain.")
        except SenzaDomainsError as e:
            self.logger.exception("Failed to get domains. Traffic will"
                                  "not be switched.", extra=self.log_info)
            raise TrafficNotUpdated(e.message)
        except SenzaTrafficError as e:
            self.logger.exception("Failed to switch app traffic.",
                                  extra=self.log_info)
            raise TrafficNotUpdated(e.message)

    def update_ami_image(self, new_ami_image: str):
        """Change the AMI image of the Auto Scaling Group (ASG) and respawn the
        instances to use new image.

        :param new_ami_image: specified image (AMI ID or "latest")
        :raises AMIImageNotUpdated: when a unexpected error occour while
                                    running the senza commands.
        """
        try:

            self.senza.patch(self.stack.stack_name, self.stack.stack_version,
                             new_ami_image)
            self.senza.respawn_instances(self.stack.stack_name,
                                         self.stack.stack_version)

        except ExecutionError as e:
            self.logger.info(e.message, extra=self.log_info)
            raise AMIImageNotUpdated(e.message)

    def delete_stack(self) -> None:
        """
        Delete the stack.

        :raises: StackDeleteException
        """
        self.logger.info("Removing stack...", extra=self.log_info)

        try:
            self.senza.remove(self.stack.stack_name, self.stack.stack_version)
            self.logger.info("Stack removed.", extra=self.log_info)
        except ExecutionError as e:
            self.logger.exception("Failed to remove stack.",
                                  extra=self.log_info)
            raise StackDeleteException(e.output)
