import logging
from unittest.mock import MagicMock

import pytest

from fixtures.senza import mock_senza  # NOQA


@pytest.fixture(scope='session')
def debug_level():
    logging.getLogger().setLevel(logging.DEBUG)
