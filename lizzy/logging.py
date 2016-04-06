from pprint import pformat
from typing import Any, Union
import datetime
import logging
import traceback


ROOT_LOGGER = logging.getLogger('')

# the following keys will be ignored
DEFAULT_LOG_RECORD_KEYS = (
    'filename', 'levelno', 'lineno', 'msecs', 'threadName', 'exc_text', 'msg', 'name', 'processName', 'thread',
    'relativeCreated', 'process', 'exc_info', 'args', 'created', 'pathname', 'funcName', 'levelname', 'module',
    'stack_info')


class DefaultFormatter(logging.Formatter):
    @staticmethod
    def format_kv(key: str, value: Any) -> str:
        if not isinstance(value, str):
            value = pformat(value, width=100)  # type: str
        if not value:
            return '\n     > {key}: ************ EMPTY ************'.format(key=key)
        value_lines = value.splitlines()
        first_value_line = value_lines.pop(0)
        lines = ['\n     > {key}: {value}'.format(key=key, value=first_value_line)]
        for line in value_lines:
            spaces = ' ' * (9 + len(key))
            lines.append('\n{spaces}{line}'.format(spaces=spaces, line=line))

        return ''.join(lines)

    def format(self, record: logging.LogRecord) -> str:
        record_values = vars(record)
        msg = str(record.msg) % record.args
        message = '{level:>5}: {msg}'.format(level=record.levelname, msg=msg)

        extra = {key: value for key, value in record_values.items() if key not in DEFAULT_LOG_RECORD_KEYS}
        extra_lines = [self.format_kv(key, value) for key, value in extra.items()]

        if record.exc_info:
            trace = '\n'.join(traceback.format_tb(record.exc_info[2]))
            exception = str(record.exc_info[1])
            exception_lines = [self.format_kv('Traceback', trace)]
            if exception:
                exception_lines.append(self.format_kv('Exception', exception))
        else:
            exception_lines = []

        components = [message]
        components.extend(extra_lines)
        components.extend(exception_lines)
        log_line = ''.join(components)

        return log_line


class DebugFormatter(logging.Formatter):
    @staticmethod
    def format_kv(key: str, value: Any, error: bool=False) -> str:
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

    def format(self, record: logging.LogRecord) -> str:
        record_values = vars(record)
        date_time = '\033[1m\033[34m{}\033[0m'.format(datetime.datetime.fromtimestamp(record.created).isoformat())
        log_level = '\033[1m {: <5} │ \033[0m'.format(record.levelname)
        msg = str(record.msg) % record.args

        extra = {key: value for key, value in record_values.items() if key not in DEFAULT_LOG_RECORD_KEYS}
        extra_lines = [self.format_kv(key, value) for key, value in extra.items()]

        if record.exc_info:
            trace = '\n'.join(traceback.format_tb(record.exc_info[2]))
            exception = str(record.exc_info[1])
            exception_lines = [self.format_kv('Traceback', trace, True)]
            if exception:
                exception_lines.append(self.format_kv('Exception', exception, True))
        else:
            exception_lines = []

        components = [date_time, log_level, msg]
        components.extend(extra_lines)
        components.extend(exception_lines)
        log_line = ''.join(components)

        return log_line


def init_logging(log_format: str='default', level: str='INFO') -> Union[DefaultFormatter, DebugFormatter]:
    """
    Initializes the logging.

    Format can be either 'default' for a simple formatter and 'human' for a colorful format.

    :param log_format: Selected format
    :param level: Log level
    :return: Selected Formatter
    """
    stream_handler = logging.StreamHandler()
    if log_format == 'default':
        formatter = DefaultFormatter
    elif log_format == 'human':
        formatter = DebugFormatter
    else:
        raise ValueError('Unrecognized Format: {}'.format(log_format))
    stream_handler.setFormatter(formatter())
    ROOT_LOGGER.addHandler(stream_handler)
    ROOT_LOGGER.setLevel(level)
    return formatter


def logger(name):
    logger_instance = logging.getLogger(name)
    logger_instance.parent = ROOT_LOGGER
    return logger_instance
