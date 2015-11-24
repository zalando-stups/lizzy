from unittest.mock import MagicMock, call, ANY

from lizzy.apps.common import ExecutionError
from lizzy.job import check_status

SENZA_STACKS = [{'stack_name': 'stack', 'version': 1},
                {'stack_name': 'stacknotinlizzy', 'version': 1},
                {'stack_name': 'lizzyremoved', 'version': 1}]

LIZZY_STACKS = {'stack-1': {'stack_id': 'stack-1',
                            'creation_time': '2015-09-15',
                            'keep_stacks': 1,
                            'traffic': 100,
                            'image_version': 'version',
                            'senza_yaml': 'yaml',
                            'stack_name': 'stackno1',
                            'stack_version': 'v1',
                            'status': 'LIZZY:NEW',
                            'parameters': ['parameter1', 'parameter2']},
                'lizzyremoved-1': {'stack_id': 'lizzyremoved-1',
                                   'creation_time': '2015-09-15',
                                   'keep_stacks': 1,
                                   'traffic': 100,
                                   'image_version': 'version',
                                   'senza_yaml': 'yaml',
                                   'stack_name': 'stackno1',
                                   'stack_version': 'v1',
                                   'status': 'LIZZY:REMOVED',
                                   'parameters': ['parameter1', 'parameter2']}}


class FakeStack:
    # TODO Implement some stacks

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    @classmethod
    def all(cls):
        return [cls(**stack) for stack in LIZZY_STACKS.values()]

    @classmethod
    def get(cls, item):
        return cls(**LIZZY_STACKS[item])

    def lock(self, n):
        return True

    def unlock(self):
        return True

    def save(self):
        return True


def test_check_status(monkeypatch):
    mock_stack = MagicMock()
    mock_stack.all.return_value = [FakeStack(**stack) for stack in LIZZY_STACKS.values()]
    monkeypatch.setattr('lizzy.job.Stack', FakeStack)

    mock_senza = MagicMock()
    mock_senza.return_value = mock_senza
    mock_senza.list.return_value = SENZA_STACKS
    monkeypatch.setattr('lizzy.job.Senza', mock_senza)

    mock_deployer = MagicMock()
    mock_deployer.return_value = mock_deployer
    monkeypatch.setattr('lizzy.job.Deployer', mock_deployer)

    mock_log = MagicMock()
    monkeypatch.setattr('lizzy.job.logger', mock_log)

    check_status('abc')
    assert mock_senza.called
    assert mock_senza.list.called

    mock_deployer.assert_any_call('abc', ANY, ANY, ANY)
    assert mock_deployer.call_count == 1
    mock_deployer.handle.assert_any_call()
    assert mock_deployer.handle.call_count == 1

    mock_log.debug.assert_any_call("In Job")
    mock_log.debug.assert_any_call('Stack found.', extra={'lizzy.stack.id': 'stack-1'})
    mock_log.debug.assert_any_call('Stack found.', extra={'lizzy.stack.id': 'lizzyremoved-1'})


def test_fail_get_list(monkeypatch):
    mock_stack = MagicMock()
    mock_stack.all.return_value = []
    monkeypatch.setattr('lizzy.job.Stack', mock_stack)

    mock_senza = MagicMock()
    mock_senza.return_value = mock_senza
    mock_senza.list.side_effect = ExecutionError(1, 'error raised by test')
    monkeypatch.setattr('lizzy.job.Senza', mock_senza)

    mock_log = MagicMock()
    monkeypatch.setattr('lizzy.job.logger', mock_log)

    check_status('abc')
    assert mock_stack.all.called
    assert mock_senza.called
    assert mock_senza.list.called

    assert mock_log.debug.call_args_list == [call('In Job')]
    mock_log.exception.assert_any_call("Couldn't get CF stacks. Exiting Job.")
