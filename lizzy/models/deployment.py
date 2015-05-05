import logging
import datetime
import random

import rod.model


logger = logging.getLogger('lizzy.model.deployment')


class Deployment(rod.model.Model):

    prefix = 'lizzy_deployment'
    key = 'deployment_id'
    search_properties = ['deployment_id']

    def __init__(self, *,
                 deployment_id: str=None,
                 deployment_strategy: str,
                 image_version: str,
                 senza_yaml: str,
                 stack_name: str,
                 stack_version: str=None,
                 status: str='LIZZY_NEW',
                 **kwargs):
        self.stack_name = stack_name
        self.stack_version = stack_version if stack_version is not None else self.generate_version()
        self.deployment_id = deployment_id if deployment_id is not None else self.generate_id()
        self.deployment_strategy = deployment_strategy
        self.image_version = image_version
        self.senza_yaml = senza_yaml
        self.status = status  # status is cloud formation status or LIZZY_NEW

    @staticmethod
    def generate_version() -> str:
        now = datetime.datetime.utcnow()
        random_part = random.randint(0, 99)
        return '{time:%y%m%d%H%M%S}-{rand:02}'.format(time=now, rand=random_part)

    def generate_id(self) -> str:
        """
        The id will be the same as the stack name on aws
        """
        return '{name}-{version}'.format(name=self.stack_name, version=self.stack_version)
