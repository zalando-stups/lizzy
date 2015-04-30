import uuid

import rod.model
import yaml


class Deployment(rod.model.Model):

    prefix = 'lizzy_deployment'
    key = 'deployment_id'
    search_properties = ['deployment_id']

    def __init__(self, *,
                 deployment_id: str=None,
                 deployment_strategy: str,
                 image_version: str,
                 senza_yaml: str,
                 stack_name: str=None,
                 status: str='LIZZY_NEW',
                 **kwargs):
        self.deployment_id = deployment_id if deployment_id is not None else str(uuid.uuid1())
        self.deployment_strategy = deployment_strategy
        self.image_version = image_version
        self.senza_yaml = senza_yaml
        if stack_name is None:
            # TODO: error handling
            senza_definition = yaml.safe_load(senza_yaml)
            self.stack_name = senza_definition['SenzaInfo']['StackName']
        else:
            self.stack_name = stack_name
        self.status = status  # status is cloud formation status or LIZZY_NEW

    def as_dict(self):
        return self.__dict__
