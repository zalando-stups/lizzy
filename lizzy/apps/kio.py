from typing import Iterable
import json
import logging
import subprocess

from .common import ExecutionError

logger = logging.getLogger('lizzy.kio')


class Kio:
    @classmethod
    def versions_create(cls, application_id: str, version: str, artifact: str) -> bool:
        try:
            cls._execute('versions', 'create', '-m', '"Created by Lizzy"', application_id, version, artifact)
            return True
        except ExecutionError as e:
            logger.error('Failed to create version.', extra={'command.output': e.output})
            return False

    @staticmethod
    def _execute(subcommand: str, *args: Iterable[str], expect_json: bool=False):
        command = ['kio', subcommand]
        if expect_json:
            command += ['-o', 'json']
            stderr_to = subprocess.PIPE
        else:
            stderr_to = subprocess.STDOUT
        command += args
        logger.debug('Executing kio.', extra={'command': ' '.join(command)})
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=stderr_to)
        stdout, _ = process.communicate()
        output = stdout.decode()
        if process.returncode == 0:
            if expect_json:
                try:
                    return json.loads(output)
                except ValueError:
                    raise ExecutionError('JSON ERROR', output)
            else:
                return output
        else:
            logger.error("Error executing command.", extra={'command': ' '.join(command),
                                                            'command.output': output.strip()})
            raise ExecutionError(process.returncode, output)
