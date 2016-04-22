from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_senza(monkeypatch):
    mock = MagicMock()
    mock.return_value = mock
    mock.list = lambda *a, **k: [{"creation_time": 1460635167,
                                  "description": "Lizzy Bus (ImageVersion: 257)",
                                  "stack_name": "lizzy-bus",
                                  "status": "CREATE_COMPLETE",
                                  "version": "257"}]
    monkeypatch.setattr('lizzy.api.Senza', mock)
    return mock
