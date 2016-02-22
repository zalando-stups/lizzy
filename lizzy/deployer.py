
from lizzy.apps.senza import Senza
from lizzy.models.stack import Stack
from lizzy.logging import logger
from lizzy.configuration import config
from lizzy.exceptions import AIMImageNotUpdated, ExecutionError


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

    def update_aim_image(self, new_aim_image: str):
        """Change the AIM image of the Auto Scaling Group (ASG) and respawn the
        instances to use new image.

        :param new_aim_image: specified image (AMI ID or "latest")
        :raises AIMImageNotUpdated: when a unexpected error occour while
                                    running the senza commands.
        """
        try:

            self.senza.patch(self.stack.stack_name, self.stack.stack_version,
                             new_aim_image)
            self.senza.respawn_instances(self.stack.stack_name,
                                         self.stack.stack_version)

        except ExecutionError as e:
            self.logger.info(e.message, extra=self.log_info)
            raise AIMImageNotUpdated(e.message)
