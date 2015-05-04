import logging
import uuid

import rod.model
import yaml

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
                 status: str='LIZZY_NEW',
                 **kwargs):
        self.deployment_id = deployment_id if deployment_id is not None else str(uuid.uuid1())
        self.deployment_strategy = deployment_strategy
        self.image_version = image_version
        self.senza_yaml = senza_yaml
        self.status = status  # status is cloud formation status or LIZZY_NEW

        # TODO validate
        self._senza_definition = yaml.safe_load(senza_yaml)

    @property
    def stack_name(self) -> str:
        # TODO error handling
        try:
            return self._senza_definition['SenzaInfo']['StackName']
        except Exception:
            logger.exception("Couldn't get stack name for:\n%s", str(self._senza_definition))
            return ''
