from collections import OrderedDict
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
        values['logger'] = record.name  # The name of the logger used to log the event represented
        values['log_level'] = record.levelname  # Text logging level for the message
        values['time'] = datetime.datetime.fromtimestamp(record.created).isoformat()
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


def init_logging():
    root_logger = logging.getLogger('')
    sh = logging.StreamHandler()
    sh.setFormatter(JsonFormatter())
    root_logger.addHandler(sh)
    root_logger.setLevel(logging.DEBUG)

    logger = logging.getLogger('lizzy')

    return logger
