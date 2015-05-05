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


class Senza:

    region = 'eu-west-1'

    @classmethod
    def create(cls, senza_yaml: str, stack_version: str, image_version: str) -> bool:
        with tempfile.NamedTemporaryFile() as temp_yaml:
            temp_yaml.write(senza_yaml.encode())
            temp_yaml.file.flush()
            error = cls._execute('create', temp_yaml.name, stack_version, image_version)
        return not error

    @classmethod
    def list(cls) -> list:
        """
        Returns the stack list
        """
        stacks = cls._execute('list', expect_json=True)
        return stacks

    @classmethod
    def _execute(cls, *args, expect_json: bool=False):
        command = ['senza']
        command += args
        command += ['--region', cls.region]
        if expect_json:
            command += ['-o', 'json']
        logger.debug('%s', command)
        process = subprocess.Popen(command, stdout=subprocess.PIPE)
        stdout, _ = process.communicate()
        if expect_json:
            return json.loads(stdout.decode())
        else:
            return process.returncode
