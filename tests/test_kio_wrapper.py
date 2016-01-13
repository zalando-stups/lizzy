from unittest.mock import MagicMock

import pytest

from lizzy.apps.kio import Kio
from lizzy.apps.common import ExecutionError


@pytest.fixture
def popen(monkeypatch):
    mock_popen = MagicMock()
    mock_popen.return_value = mock_popen
    mock_popen.returncode = 0
    mock_popen.communicate.return_value = b'{"stream": "stdout"}', b'stderr'
    monkeypatch.setattr('lizzy.apps.common.Popen', mock_popen)
    return mock_popen


def test_create(monkeypatch, popen):
    kio = Kio()
    kio.logger = MagicMock()
    kio.versions_create('app', '42', 'my_super_cool:docker_image')

    popen.assert_called_with(['kio', 'versions', 'create',
                              '-m', '"Created by Lizzy"',
                              'app', '42', 'my_super_cool:docker_image'],
                             stdout=-1,
                             stderr=-2)

    cmd = 'kio versions create -m "Created by Lizzy" app 42 my_super_cool:docker_image'
    kio.logger.debug.assert_called_with('Executing %s.', 'kio', extra={'command': cmd})
    assert not kio.logger.error.called

    popen.returncode = 1
    kio.logger.reset_mock()

    kio.versions_create('app', '42', 'my_super_cool:docker_image')
    kio.logger.error.assert_called_with('Failed to create version.', extra={'command.output': '{"stream": "stdout"}'})
