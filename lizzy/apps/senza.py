from typing import Optional, List, Dict
import pystache
import tempfile
import yaml

from .common import ExecutionError, Application


class Senza(Application):
    def __init__(self, region: str):
        super().__init__('senza', extra_parameters=['--region', region])

    @staticmethod
    def generate_definition(definition: str, version: str, parameters: List[str]) -> dict:
        # TODO: error handling
        raw_definition = yaml.load(definition)  # type: dict
        senza_info = raw_definition['SenzaInfo']  # type: dict
        senza_paramaters = senza_info['Parameters']  # type: List[Dict[str, Dict[str, str]]]

        # TODO support default
        # TODO support named parameters
        parameter_map = {}
        for value in parameters:
            definition_parameter = senza_paramaters.pop(0)
            name = list(definition_parameter.keys()).pop()
            default = definition_parameter[name].get('default', None)  # TODO sentinel
            parameter_map[name] = value

        render = pystache.Renderer(missing_tags='strict')
        final_defintion = render.render(definition, {'Arguments': parameter_map})
        return yaml.load(final_defintion)

    def create(self, senza_yaml: str, stack_version: str, image_version: str, parameters: List[str]) -> bool:
        """
        Create a new stack

        :param senza_yaml: Senza Definition
        :param stack_version: New stack's version
        :param image_version: Docker image to deployed
        :param parameters: Extra parameters for the deployment
        :return: Success of the operation
        """
        with tempfile.NamedTemporaryFile() as temp_yaml:
            temp_yaml.write(senza_yaml.encode())
            temp_yaml.file.flush()
            try:
                self._execute('create', '--force', temp_yaml.name, stack_version, image_version, *parameters)
                return True
            except ExecutionError as exception:
                self.logger.error('Failed to create stack.', extra={'command.output': exception.output})
                return False

    def domains(self, stack_name: Optional[str]=None) -> List[Dict[str, str]]:
        """
        Get domain names for applications. If stack name is provided then it will show the domain names just for that
        application

        :param stack_name: Name of the application stack
        :return: Route53 Domains
        """
        if stack_name:
            stack_domains = self._execute('domains', stack_name, expect_json=True)
        else:
            stack_domains = self._execute('domains', expect_json=True)
        return stack_domains

    def list(self) -> List[Dict]:
        """
        Returns a list of all the stacks
        """
        stacks = self._execute('list', expect_json=True)  # type: list
        return stacks

    def remove(self, stack_name: str, stack_version: str) -> bool:
        """
        Removes a stack

        :param stack_name: Name of the application stack
        :param stack_version: Name of the application version that will be removed
        :return: Success of the operation
        """
        try:
            self._execute('delete', stack_name, stack_version)
            return True
        except ExecutionError as exception:
            self.logger.error('Failed to delete stack.', extra={'command.output': exception.output})
            return False

    def traffic(self, stack_name: str, stack_version: str, percentage: int) -> List[Dict]:
        """
        Changes the application traffic percentage.

        :param stack_name: Name of the application stack
        :param stack_version: Name of the application version that will be changed
        :param percentage: New percentage
        :return: Traffic weights for the application
        """
        traffic_weights = self._execute('traffic', stack_name, stack_version, str(percentage), expect_json=True)
        return traffic_weights
