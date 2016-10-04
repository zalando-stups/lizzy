import json
from logging import getLogger
from subprocess import PIPE, STDOUT, Popen
from typing import Iterable, Optional

from .. import sentry_client
from ..exceptions import ExecutionError


class Application:  # pylint: disable=too-few-public-methods
    def __init__(self, application: str,
                 extra_parameters: Optional[Iterable[str]]=None):
        self.logger = getLogger('lizzy.app.{}'.format(application))
        self.application = application
        self.extra_parameters = extra_parameters or []  # type: Iterable[str]

    def _execute(self, subcommand: str, *args: Iterable[str],
                 expect_json: bool=False,
                 accept_empty: bool=True):
        command = [self.application, subcommand]
        command.extend(self.extra_parameters)
        if expect_json:
            command += ['-o', 'json']
            stderr_to = PIPE
        else:
            stderr_to = STDOUT
        command += args
        command = [arg for arg in command if arg is not None]
        self.logger.debug('Executing %s.', self.application,
                          extra={'command': ' '.join(command)})
        process = Popen(command, stdout=PIPE, stderr=stderr_to)
        stdout, stderr = process.communicate()
        output = stdout.decode()
        sentry_client.capture_breadcrumb(data={
            'command': ' '.join(command),
            'command_return_code': process.returncode,
            'output': output
        })
        if process.returncode == 0:
            if expect_json and (output or not accept_empty):
                try:
                    return json.loads(output)
                except ValueError:
                    raise ExecutionError('JSON ERROR', output)
            elif not output and not accept_empty:
                raise ExecutionError('EMPTY OUTPUT', output)
            else:
                return output
        else:
            if expect_json:
                output += '\n' + stderr.decode()
            self.logger.error("Error executing command.",
                              extra={'command': ' '.join(command),
                                     'command.output': output.strip()})
            raise ExecutionError(process.returncode, output)
