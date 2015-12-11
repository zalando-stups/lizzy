import tempfile

from .common import ExecutionError, Application


class Senza(Application):
    def __init__(self, region: str):
        super().__init__('senza', extra_parameters=['--region', region])

    def create(self, senza_yaml: str, stack_version: str, image_version: str, parameters: list) -> bool:
        with tempfile.NamedTemporaryFile() as temp_yaml:
            temp_yaml.write(senza_yaml.encode())
            temp_yaml.file.flush()
            try:
                self._execute('create', '--force', temp_yaml.name, stack_version, image_version, *parameters)
                return True
            except ExecutionError as e:
                self.logger.error('Failed to create stack.', extra={'command.output': e.output})
                return False

    def domains(self, stack_name: str=None):
        if stack_name:
            stack_domains = self._execute('domains', stack_name, expect_json=True)
        else:
            stack_domains = self._execute('domains', expect_json=True)
        return stack_domains

    def list(self) -> list:
        """
        Returns the stack list
        """
        stacks = self._execute('list', expect_json=True)
        return stacks

    def remove(self, stack_name: str, stack_version: str) -> bool:
        try:
            self._execute('delete', stack_name, stack_version)
            return True
        except ExecutionError as e:
            self.logger.error('Failed to delete stack.', extra={'command.output': e.output})
            return False

    def traffic(self, stack_name: str, stack_version: str, percentage: int):
        traffic_weights = self._execute('traffic', stack_name, stack_version, str(percentage), expect_json=True)
        return traffic_weights
