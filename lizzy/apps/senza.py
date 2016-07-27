import tempfile
from typing import Dict, List, Optional

from ..exceptions import (ExecutionError, SenzaDomainsError, SenzaPatchError,
                          SenzaRenderError, SenzaRespawnInstancesError,
                          SenzaTrafficError)
from ..version import VERSION
from .common import Application


class Senza(Application):
    def __init__(self, region: str):
        super().__init__('senza', extra_parameters=['--region', region])

    def create(self, senza_yaml: str, stack_version: str,
               parameters: List[str], disable_rollback: bool, dry_run: bool,
               tags: List[str]) -> str:
        """
        Create a new stack

        :param senza_yaml: Senza Definition
        :param stack_version: New stack's version
        :param parameters: Extra parameters for the deployment
        :param disable_rollback: Disables stack rollback on creation failure
        :param tags: Extra tags to add to the stack
        :return: Success of the operation
        """
        with tempfile.NamedTemporaryFile() as temp_yaml:
            temp_yaml.write(senza_yaml.encode())
            temp_yaml.file.flush()
            args = ['--force']

            if disable_rollback:
                args.append('--disable-rollback')

            if dry_run:
                args.append('--dry-run')

            cli_tags = ['-t', 'LizzyVersion={}'.format(VERSION)]
            for tag in tags:
                # Adds the tags prepended with Lizzy
                cli_tags.extend(['-t', tag])

            args.append('--stacktrace-visible')
            return self._execute('create', *args, *cli_tags, temp_yaml.name,
                                 stack_version, *parameters)

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
        except ExecutionError as exception:
            raise SenzaDomainsError(exception.error, exception.output)

    def list(self, *args, **kwargs) -> List[Dict]:
        """
        Returns a list of all the stacks
        """
        return self._execute('list', *args, **kwargs,
                             expect_json=True)  # type: list

    def remove(self, stack_id: str, dry_run: bool, force: bool) -> bool:
        """
        Removes a stack

        :param stack_name: Name of the application stack
        :param stack_version: Name of the application version that will
                              be removed
        :raises: ExecutionError
        :return: Success of the operation
        """
        # TODO rename to delete
        options = []
        if dry_run:
            options.append('--dry-run')
        if force:
            options.append('--force')
        return self._execute('delete', *options, *stack_id.rsplit("-", 1))

    def traffic(self, stack_name: str, stack_version: Optional[str]=None,
                percentage: Optional[int]=None) -> List[Dict]:
        """
        Changes the application traffic percentage.

        :param stack_name: Name of the application stack
        :param stack_version: Name of the application version that will be
                              changed
        :param percentage: New percentage
        :return: Traffic weights for the application
        :raises SenzaTrafficError: when a ExecutionError is thrown to allow
                                   more specific error handing.
        """
        try:
            arguments = []
            if stack_version is not None:
                arguments.append(stack_version)
            if percentage is not None:
                arguments.append(str(percentage))

            traffic_weights = self._execute('traffic', stack_name, *arguments,
                                            expect_json=True)
            return traffic_weights
        except ExecutionError as exception:
            raise SenzaTrafficError(exception.error, exception.output)

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

        except ExecutionError as exception:
            raise SenzaRespawnInstancesError(exception.error, exception.output)

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

        except ExecutionError as exception:
            raise SenzaPatchError(exception.error, exception.output)

    def render_definition(self, senza_yaml: str, stack_version: str,
                          image_version: str, parameters: List[str]):
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
            except ExecutionError as exception:
                self.logger.error('Failed to render CloudFormation defition.',
                                  extra={'command.output': exception.output})
                raise SenzaRenderError(exception.error, exception.output)
