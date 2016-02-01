from .common import ExecutionError, Application


class Kio(Application):
    def __init__(self):
        super().__init__('kio')

    def versions_create(self, application_id: str, version: str, artifact: str) -> bool:
        """
        Creates a new version in Kio

        :param application_id: ID of the application
        :param version: ID of the version
        :param artifact: Software artifact reference of this version
        :return: Success of version creation
        """
        try:
            self._execute('versions', 'create', '-m', '"Created by Lizzy"', application_id, version, artifact)
            return True
        except ExecutionError as exception:
            self.logger.error('Failed to create version.', extra={'command.output': exception.output})
            return False
