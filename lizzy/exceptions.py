from typing import Union


class LizzyError(Exception):
    """Base exception for lizzy errors."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class ExecutionError(LizzyError):
    """Raised when background command does not run as expected."""

    def __init__(self, error: Union[int, str], output: str):
        """
        :param error: Either an int error code returned by the application
                      or a text identifier
        :param output: Output of the application
        """
        self.error = error
        self.output = output.strip()
        super().__init__(str(self))

    def __str__(self):
        return '({error}): {output}'.format_map(vars(self))


class SenzaDomainsError(ExecutionError):
    """Raised when `senza domains` command returns an unexpected error."""


class SenzaTrafficError(ExecutionError):
    """Raised when `senza traffic` command returns an unexpected error."""


class SenzaRespawnInstancesError(ExecutionError):
    """Raised when `senza respawn-instances` command returns
    an unexpected error."""


class SenzaPatchError(ExecutionError):
    """Raised when `senza patch` command returns an unexpected error."""


class SenzaRenderError(ExecutionError):
    """Raised when not possible to render CloudFormation file."""


class ObjectNotFound(LizzyError):
    """Raised when model instance is not found in storage."""

    def __init__(self, uid: str):
        super().__init__("Object not found '{0}'".format(uid))
        self.uid = uid


class AMIImageNotUpdated(LizzyError):
    """Raised when 'senza patch' command to update Taupage image does
    not succeed."""


class TrafficNotUpdated(LizzyError):
    """Raised when 'senza traffic' command to update the stack traffic does
    not succeed."""
