import uuid
import rod.model as redis


class Deployment(redis.Model):

    prefix = 'lizzy_deployment'
    key = 'deployment_id'
    search_properties = ['deployment_id']

    def __init__(self, deployment_id: str=None,
                 *,
                 deployment_strategy: str=None,
                 image_version: str=None,
                 senza_yaml: str=None):
        self.deployment_id = deployment_id if deployment_id is not None else str(uuid.uuid1())
        # TODO if uid load else validate
        self.image_version = image_version
        self.deployment_strategy = deployment_strategy
        self.senza_yaml = senza_yaml

    def as_dict(self):
        return self.__dict__