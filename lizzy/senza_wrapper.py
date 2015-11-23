"""
Copyright 2015 Zalando SE

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the
License. You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific
 language governing permissions and limitations under the License.
"""

import json
import logging
import subprocess
import tempfile

logger = logging.getLogger('lizzy.senza')


class ExecutionError(Exception):
    def __init__(self, error_code: int, output: str):
        self.error_code = error_code
        self.output = output.strip()

    def __str__(self):
        return '({error_code}): {output}'.format_map(vars(self))


class Senza:
    def __init__(self, region: str):
        self.region = region

    def create(self, senza_yaml: str, stack_version: str, image_version: str, parameters: list) -> bool:
        with tempfile.NamedTemporaryFile() as temp_yaml:
            temp_yaml.write(senza_yaml.encode())
            temp_yaml.file.flush()
            try:
                self._execute('create', '--force', temp_yaml.name, stack_version, image_version, *parameters)
                return True
            except ExecutionError as e:
                logger.error('Failed to create stack.', extra={'command.output': e.output})
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
            logger.error('Failed to delete stack.', extra={'command.output': e.output})
            return False

    def traffic(self, stack_name: str, stack_version: str, percentage: int):
        traffic_weights = self._execute('traffic', stack_name, stack_version, str(percentage), expect_json=True)
        return traffic_weights

    def _execute(self, subcommand, *args, expect_json: bool=False):
        command = ['senza', subcommand]
        command += ['--region', self.region]
        if expect_json:
            command += ['-o', 'json']
            stderr_to = subprocess.PIPE
        else:
            stderr_to = subprocess.STDOUT
        command += args
        logger.debug('Executing senza.', extra={'command': ' '.join(command)})
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
