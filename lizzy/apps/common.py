from typing import Union


class ExecutionError(Exception):
    def __init__(self, error: Union[int, str], output: str):
        """
        :param error: Either an int error code returned by the application or a text identifier
        :param output: Output of the application
        """
        self.error = error
        self.output = output.strip()

    def __str__(self):
        return '({error}): {output}'.format_map(vars(self))
