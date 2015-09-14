from unittest.mock import MagicMock
import pytest
import logging

from lizzy.job import check_status
from lizzy.senza_wrapper import ExecutionError
from lizzy.models.stack import Stack

logging.basicConfig(level=logging.DEBUG)

STACKS = {'stack1': {'stack_id': None,
                     'creation_time': None,
                     'keep_stacks': 1,
                     'traffic': 100,
                     'image_version': 'version',
                     'senza_yaml': 'yaml',
                     'stack_name': 'stackno1',
                     'stack_version': 'v1',
                     'status': 'LIZZY:NEW', }}


class FakeStack(Stack):
    # TODO Implement some stacks

    @classmethod
    def all(cls):
        return []

    def delete(self):
        pass

    @classmethod
    def get(cls, uid):
        stack = STACKS[uid]
        return cls(**stack)

    def save(self):
        pass


@pytest.fixture
def fake_stacks(monkeypatch):
    monkeypatch.setattr('lizzy.job.Stack', FakeStack)


@pytest.fixture()
def fake_senza_fail(monkeypatch):
    class SenzaFail:
        def __init__(self, region):
            self.region = region

        def list(self):
            raise ExecutionError(1, 'error test')

    monkeypatch.setattr('lizzy.job.Senza', SenzaFail)


def test_fail_get_list(monkeypatch, capfd):
    mock_stack = MagicMock()
    mock_stack.all.return_value = []
    monkeypatch.setattr('lizzy.job.Stack', mock_stack)

    mock_senza = MagicMock()
    mock_senza.return_value = mock_senza
    mock_senza.list.side_effect = ExecutionError(1, 'error raised by test')
    monkeypatch.setattr('lizzy.job.Senza', mock_senza)
    check_status('abc')
    assert mock_stack.all.called
    assert mock_senza.called
    assert mock_senza.list.called
    _, log = capfd.readouterr()

    assert 'In Job' in log
    assert "Couldn't get CF stacks. Exiting Job." in log
    assert "error raised by test" in log
