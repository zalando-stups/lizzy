from unittest.mock import MagicMock
from lizzy.apps.senza import Senza

import pytest


@pytest.fixture
def mock_senza(monkeypatch):
    mock = MagicMock()
    mock.return_value = mock

    def list_method(*a, **k):
        return [{"creation_time": 1460635167,
                 "description": "Lizzy Bus (ImageVersion: 257)",
                 "stack_name": "lizzy-bus" if not a else a[0],
                 "status": "CREATE_COMPLETE",
                 "version": "257" if not a else a[1]}]

    mock.list = MagicMock(wraps=list_method)
    mock.create = MagicMock(return_value="output")
    monkeypatch.setattr('lizzy.api.Senza', mock)
    monkeypatch.setattr('lizzy.models.stack.Senza', mock)
    return mock
