from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_aws(monkeypatch):
    mock = MagicMock()
    mock.return_value = mock

    monkeypatch.setattr('lizzy.api.AWS', mock)
    return mock
