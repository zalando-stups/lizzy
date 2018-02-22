import logging
from unittest.mock import MagicMock

import pytest

from fixtures.senza import mock_senza  # NOQA
from fixtures.aws import mock_aws  # NOQA


@pytest.fixture(scope='session')
def debug_level():
    logging.getLogger().setLevel(logging.DEBUG)


@pytest.fixture(autouse=True)
def mock_token(monkeypatch):
    monkeypatch.setattr('metricz.metricz.tokens.get', MagicMock(return_value='abc'))
