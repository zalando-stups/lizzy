from collections import OrderedDict
from pprint import pformat
import datetime
import json
import logging
import traceback

# the following keys will be ignored unless specifically added
DEFAULT_LOG_RECORD_KEYS = (
    'filename', 'levelno', 'lineno', 'msecs', 'threadName', 'exc_text', 'msg', 'name', 'processName', 'thread',
    'relativeCreated', 'process', 'exc_info', 'args', 'created', 'pathname', 'funcName', 'levelname', 'module',
    'stack_info')


class JsonFormatter(logging.Formatter):
    need_quoting = [' ', '/', '"', '\'']

    def format(self, record: logging.LogRecord):
        record_values = vars(record)

        values = OrderedDict()
        values['time'] = datetime.datetime.fromtimestamp(record.created).isoformat()
        values['logger'] = record.name  # The name of the logger used to log the event represented
        values['log_level'] = record.levelname  # Text logging level for the message
        values['function'] = '{}.{}'.format(record.module, record.funcName)
        values['line'] = record.lineno
        try:
            values['msg'] = str(record.msg) % record.args
        except Exception as e:  # pragma: no cover
            values['LOGGING_ERROR'] = str(e)

        # if there is an exception convert to string
        if vars(record)['exc_info']:
            exc_info = record_values['exc_info']
            values['traceback'] = ''.join(traceback.format_tb(exc_info[2]))
            values['exception'] = str(exc_info[1]).strip()

        # extra
        extra = {key: value for key, value in record_values.items() if key not in DEFAULT_LOG_RECORD_KEYS}
        values.update(extra)

        log_line = json.dumps(values, default=repr)

        return log_line


class DebugFormatter(logging.Formatter):
    @staticmethod
    def format_kv(key, value, error=False):
        color = 31 if error else 32
        if not isinstance(value, str):
            value = pformat(value, width=120)  # type: str
        value_lines = value.splitlines()
        first_value_line = value_lines.pop(0)
        lines = ['\n{: >32} │ \033[{}m{}\033[0m'.format(key, color, first_value_line)]
        for line in value_lines:
            lines.append('\n                                 │ \033[{}m{}\033[0m'.format(color, line))

        return ''.join(lines)

    def format(self, record: logging.LogRecord):
        record_values = vars(record)
        date_time = '\033[1m\033[34m{}\033[0m'.format(datetime.datetime.fromtimestamp(record.created).isoformat())
        log_level = '\033[1m {: <5} │ \033[0m'.format(record.levelname)
        msg = str(record.msg) % record.args

        extra = {key: value for key, value in record_values.items() if key not in DEFAULT_LOG_RECORD_KEYS}
        extra_lines = [self.format_kv(key, value) for key, value in extra.items()]

        if record.exc_info:
            tb = '\n'.join(traceback.format_tb(record.exc_info[2]))
            exception = str(record.exc_info[1])
            exception_lines = [self.format_kv('Traceback', tb, True), self.format_kv('Exception', exception, True)]
        else:
            exception_lines = []

        components = [date_time, log_level, msg]
        components.extend(extra_lines)
        components.extend(exception_lines)
        log_line = ''.join(components)

        return log_line


def init_logging(format='json'):
    root_logger = logging.getLogger('')
    sh = logging.StreamHandler()
    if format == 'json':
        sh.setFormatter(JsonFormatter())
    elif format == 'human':
        sh.setFormatter(DebugFormatter())
    root_logger.addHandler(sh)
    root_logger.setLevel(logging.DEBUG)
