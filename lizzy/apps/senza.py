from typing import Optional, List, Dict
import tempfile

from ..version import VERSION
from .common import Application
from ..exceptions import (ExecutionError, SenzaDomainsError, SenzaTrafficError,
                          SenzaRespawnInstancesError, SenzaPatchError,
                          SenzaRenderError)


class Senza(Application):
    def __init__(self, region: str):
        super().__init__('senza', extra_parameters=['--region', region])

    def create(self, senza_yaml: str, stack_version: str, image_version: str,
               parameters: List[str], disable_rollback: bool) -> bool:
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
                args = ['--force']
                if disable_rollback:
                    args.append('--disable-rollback')

                parameters.extend(['-t', 'LizzyVersion={}'.format(VERSION)])

                self._execute('create', *args, temp_yaml.name, stack_version,
                              image_version, *parameters)

                return True
            except ExecutionError as exception:
                self.logger.error('Failed to create stack.',
                                  extra={'command.output': exception.output})
                return False

    def domains(self, stack_name: Optional[str]=None) -> List[Dict[str, str]]:
        """
        Get domain names for applications. If stack name is provided then it
        will show the domain names just for that application

        :param stack_name: Name of the application stack
        :return: Route53 Domains
        :raises SenzaDomainError: when a ExecutionError is thrown to allow more
                                  specific error handing.
        """
        try:
            if stack_name:
                stack_domains = self._execute('domains', stack_name,
                                              expect_json=True)
            else:
                stack_domains = self._execute('domains', expect_json=True)
            return stack_domains
        except ExecutionError as e:
            raise SenzaDomainsError(e.error, e.output)

    def list(self) -> List[Dict]:
        """
        Returns a list of all the stacks
        """
        return self._execute('list', expect_json=True)  # type: list

    def remove(self, stack_name: str, stack_version: str) -> bool:
        """
        Removes a stack

        :param stack_name: Name of the application stack
        :param stack_version: Name of the application version that will be removed
        :raises: ExecutionError
        :return: Success of the operation
        """
        self._execute('delete', stack_name, stack_version)
        return True

    def traffic(self, stack_name: str, stack_version: str, percentage: int) -> List[Dict]:
        """
        Changes the application traffic percentage.

        :param stack_name: Name of the application stack
        :param stack_version: Name of the application version that will be changed
        :param percentage: New percentage
        :return: Traffic weights for the application
        :raises SenzaTrafficError: when a ExecutionError is thrown to allow more specific error handing.
        """
        try:
            traffic_weights = self._execute('traffic', stack_name, stack_version, str(percentage), expect_json=True)
            return traffic_weights
        except ExecutionError as e:
            raise SenzaTrafficError(e.error, e.output)

    def respawn_instances(self, stack_name: str, stack_version: str):
        """
        Replace all EC2 instances in Auto Scaling Group(s).

        :param stack_name: Name of the application stack
        :param stack_version: Name of the application version that will
                              be changed
        :raises SenzaRespawnInstancesError: when a ExecutionError is thrown
                                            to allow more specific error handing.
        """
        try:

            self._execute('respawn-instances', stack_name, stack_version,
                          expect_json=True)

        except ExecutionError as e:
            raise SenzaRespawnInstancesError(e.error, e.output)

    def patch(self, stack_name: str, stack_version: str, ami_image: str):
        """
        Patch specific properties of existing stack.

        :param stack_name: Name of the application stack
        :param stack_version: Name of the application version that will
                              be changed
        :param ami_image: Specified image (AMI ID or "latest")
        :raises SenzaPatchError: when a ExecutionError is thrown to allow more
                                 specific error handing.
        """
        try:

            image_argument = '--image={}'.format(ami_image)
            self._execute('patch', stack_name, stack_version, image_argument,
                          expect_json=True)

        except ExecutionError as e:
            raise SenzaPatchError(e.error, e.output)

    def render_definition(self, senza_yaml: str, stack_version: str, image_version: str,
                          parameters: List[str]):
        """
        Renders the cloud formation json used by senza.

        :param senza_yaml: Senza Definition
        :param stack_version: New stack's version
        :param image_version: Docker image to deployed
        :param parameters: Extra parameters for the deployment
        """
        with tempfile.NamedTemporaryFile() as temp_yaml:
            temp_yaml.write(senza_yaml.encode())
            temp_yaml.file.flush()
            try:
                return self._execute('print', '--force',
                                     temp_yaml.name, stack_version,
                                     image_version, *parameters,
                                     expect_json=True)
            except ExecutionError as e:
                self.logger.error('Failed to render CloudFormation defition.',
                                  extra={'command.output': e.output})
                raise SenzaRenderError(e.error, e.output)
