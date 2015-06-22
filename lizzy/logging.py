import datetime
import logging
import traceback


class KVPFormatter(logging.Formatter):

    need_quoting = [' ', '/', '"', '\'']

    def __escape_value(self, value):
        if isinstance(value, str):
            needs_to_be_escaped = any(char in value for char in self.need_quoting)
            if needs_to_be_escaped:
                if '\"' in value:
                    value = repr(value)
                else:
                    # if value doesn't have double quotes just enclose it in double quotes
                    value = '"{value}"'.format(value=value)
        return value

    def format(self, record: logging.LogRecord):
        values = vars(record)

        # special cases
        try:
            values['msg'] = str(record.msg) % record.args
            del values['args']
        except TypeError as e:
            values['LOGGING_ERROR'] = str(e)

        values['created'] = datetime.datetime.fromtimestamp(values['created'])

        # if there is an exception convert to string
        if values['exc_info']:
            exc_info = values['exc_info']
            values['exc_info'] = exc_info and repr(exc_info)
            values['traceback'] = ''.join(traceback.format_tb(exc_info[2]))
        else:
            values['traceback'] = None

        log_line = ' '.join('{key}={value}'.format(key=key, value=self.__escape_value(value))
                            for key, value
                            in values.items())

        if values['traceback']:  # include traceback in human readable format
            traceback.print_exc()

        return log_line


def init_logging():
    root_logger = logging.getLogger('')
    sh = logging.StreamHandler()
    sh.setFormatter(KVPFormatter())
    root_logger.addHandler(sh)
    root_logger.setLevel(logging.DEBUG)

    logger = logging.getLogger('lizzy')

    return logger
