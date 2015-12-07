from pprint import pformat
import datetime
import logging
import traceback

# the following keys will be ignored
DEFAULT_LOG_RECORD_KEYS = (
    'filename', 'levelno', 'lineno', 'msecs', 'threadName', 'exc_text', 'msg', 'name', 'processName', 'thread',
    'relativeCreated', 'process', 'exc_info', 'args', 'created', 'pathname', 'funcName', 'levelname', 'module',
    'stack_info')


class DefaultFormatter(logging.Formatter):

    @staticmethod
    def format_kv(key, value, error=False):
        if not isinstance(value, str):
            value = pformat(value, width=100)  # type: str
        if not value:
            return '\n     > {key}: ************ EMPTY ************'.format(key=key)
        value_lines = value.splitlines()
        first_value_line = value_lines.pop(0)
        lines = ['\n     > {key}: {value}'.format(key=key, value=first_value_line)]
        for line in value_lines:
            spaces = ' ' * (9+len(key))
            lines.append('\n{spaces}{line}'.format(spaces=spaces, line=line))

        return ''.join(lines)

    def format(self, record: logging.LogRecord):
        record_values = vars(record)
        msg = str(record.msg) % record.args
        message = '{level:>5}: {msg}'.format(level=record.levelname, msg=msg)

        extra = {key: value for key, value in record_values.items() if key not in DEFAULT_LOG_RECORD_KEYS}
        extra_lines = [self.format_kv(key, value) for key, value in extra.items()]

        if record.exc_info:
            tb = '\n'.join(traceback.format_tb(record.exc_info[2]))
            exception = str(record.exc_info[1])
            exception_lines = [self.format_kv('Traceback', tb, True)]
            if exception:
                exception_lines.append(self.format_kv('Exception', exception, True))
        else:
            exception_lines = []

        components = [message]
        components.extend(extra_lines)
        components.extend(exception_lines)
        log_line = ''.join(components)

        return log_line


class DebugFormatter(logging.Formatter):
    @staticmethod
    def format_kv(key, value, error=False):
        color = 31 if error else 32
        if not isinstance(value, str):
            value = pformat(value, width=120)  # type: str
        if not value:
            return '\n{: >32} │ \033[{}m************ EMPTY ************\033[0m'.format(key, color)
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
            exception_lines = [self.format_kv('Traceback', tb, True)]
            if exception:
                exception_lines.append(self.format_kv('Exception', exception, True))
        else:
            exception_lines = []

        components = [date_time, log_level, msg]
        components.extend(extra_lines)
        components.extend(exception_lines)
        log_line = ''.join(components)

        return log_line


def init_logging(format='default'):
    root_logger = logging.getLogger('')
    sh = logging.StreamHandler()
    if format == 'default':
        sh.setFormatter(DefaultFormatter())
    elif format == 'human':
        sh.setFormatter(DebugFormatter())
    root_logger.addHandler(sh)
    root_logger.setLevel(logging.DEBUG)
