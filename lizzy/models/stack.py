from typing import List, Optional  # NOQA  pylint: disable=unused-import

from lizzy.exceptions import ObjectNotFound

from ..apps.senza import Senza
from ..configuration import config
from ..util import timestamp_to_uct

REMOVED_STACK = object()


class Stack:
    prefix = 'lizzy_stack'
    key = 'stack_id'
    search_properties = ['stack_id']

    def __init__(self, *,
                 stack_name: str,
                 creation_time: int,
                 description: str,
                 version: str,
                 status: str):
        """
        Stack Model stored in Redis
        :param stack_name: Name of the application
        :param creation_time: Date and time of stack creation
        :param description: Stack description including parameters
        :param version: Stack Version
        :param status: Stack Status in Cloud Formation
        """
        self.stack_name = stack_name
        self.creation_time = timestamp_to_uct(creation_time)
        self.description = description
        self.version = version
        self.status = status
        self.__cf_stack = None

    @classmethod
    def get(cls, stack_name: str, stack_version: str, region: Optional[str]=None) -> 'Stack':
        stacks = cls.list(stack_name, stack_version, region=region)
        if not stacks:
            raise ObjectNotFound('{}-{}'.format(stack_name, stack_version))
        else:
            return stacks[0]

    @classmethod
    def list(cls, *stack_ref: List[str], region: Optional[str]=None) -> List['Stack']:
        """
        Returns a List of stack dicts compliant with the API spec.

        .. seealso:: lizzy/swagger/lizzy.yaml#/definitions/stack
        """

        senza = Senza(region or config.region)
        stacks = [Stack(**stack)
                  for stack in senza.list(*stack_ref)]
        return stacks

    def generate_id(self) -> str:
        """
        The id will be the same as the stack name on aws
        """
        return '{name}-{version}'.format(name=self.stack_name,
                                         version=self.stack_version)
