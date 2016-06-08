from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_senza(monkeypatch):
    mock = MagicMock()
    mock.return_value = mock
    mock.list = lambda *a, **k: [{"creation_time": 1460635167,
                                  "description": "Lizzy Bus (ImageVersion: 257)",
                                  "status": "CREATE_COMPLETE",
                                  "version": "257" if not a else a[1]}]
    mock.create = MagicMock(return_value="output")
    monkeypatch.setattr('lizzy.api.Senza', mock)
    monkeypatch.setattr('lizzy.models.stack.Senza', mock)
    return mock
