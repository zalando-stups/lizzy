class ExecutionError(Exception):
    def __init__(self, error_code: int, output: str):
        self.error_code = error_code
        self.output = output.strip()

    def __str__(self):
        return '({error_code}): {output}'.format_map(vars(self))
