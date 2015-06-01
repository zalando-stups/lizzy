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

    region = 'eu-central-1'

    @classmethod
    def create(cls, senza_yaml: str, stack_version: str, image_version: str) -> bool:
        with tempfile.NamedTemporaryFile() as temp_yaml:
            temp_yaml.write(senza_yaml.encode())
            temp_yaml.file.flush()
            try:
                cls._execute('create', temp_yaml.name, stack_version, image_version)
                return True
            except ExecutionError as e:
                logger.error('Failed to create stack: %s', e.output)
                return False

    @classmethod
    def domains(cls, stack_name: str=None):
        if stack_name:
            stack_domains = cls._execute('domains', stack_name, expect_json=True)
        else:
            stack_domains = cls._execute('domains', expect_json=True)
        return stack_domains

    @classmethod
    def list(cls) -> list:
        """
        Returns the stack list
        """
        stacks = cls._execute('list', expect_json=True)
        return stacks

    @classmethod
    def remove(cls, stack_name: str, stack_version: str) -> bool:
        try:
            cls._execute('delete', stack_name, stack_version)
            return True
        except ExecutionError as e:
                logger.error('Failed to delete stack: %s', e.output)
                return False

    @classmethod
    def traffic(cls, stack_name: str, stack_version: str, percentage: int):
        traffic_weights = cls._execute('traffic', stack_name, stack_version, str(percentage), expect_json=True)
        return traffic_weights

    @classmethod
    def _execute(cls, subcommand, *args, expect_json: bool=False):
        command = ['senza', subcommand]
        command += ['--region', cls.region]
        if expect_json:
            command += ['-o', 'json']
        command += args
        logger.debug('%s', command)
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        stdout, _ = process.communicate()
        output = stdout.decode()
        if process.returncode == 0:
            if expect_json:
                return json.loads(output)
            else:
                return output
        else:
            logger.error("Error executing '%s': %s", ' '.join(command), output.strip())
            raise ExecutionError(process.returncode, output)
