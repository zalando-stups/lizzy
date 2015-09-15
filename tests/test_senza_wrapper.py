from unittest.mock import MagicMock, call, ANY, PropertyMock
import pytest
import logging

from lizzy.senza_wrapper import Senza


@pytest.fixture
def logger(monkeypatch):
    mock_log = MagicMock()
    monkeypatch.setattr('lizzy.senza_wrapper.logger', mock_log)
    return mock_log


def test_create(monkeypatch, logger):
    mock_named_tempfile = MagicMock()
    mock_tempfile = MagicMock()
    mock_tempfile.name = 'filename'
    mock_named_tempfile.__enter__.return_value = mock_tempfile
    mock_named_tempfile.return_value = mock_named_tempfile
    monkeypatch.setattr('tempfile.NamedTemporaryFile', mock_named_tempfile)

    mock_popen = MagicMock()
    mock_popen.return_value = mock_popen
    mock_popen.returncode = 0
    mock_popen.communicate.return_value = b'{"stream": "stdout"}', b'stderr'
    monkeypatch.setattr('subprocess.Popen', mock_popen)

    senza = Senza('region')
    senza.create('yaml: yaml', '10', '42', ['param1', 'param2'])

    mock_named_tempfile.assert_called_with()
    mock_tempfile.write.assert_called_with(b'yaml: yaml')

    mock_popen.assert_called_with(
        ['senza', 'create', '--region', 'region', '--force', 'filename', '10', '42', 'param1', 'param2'],
        stdout=-1,
        stderr=-2)

    cmd = 'senza create --region region --force filename 10 42 param1 param2'
    logger.debug.assert_called_with('Executing senza.', extra={'command': cmd})
    assert not logger.error.called

    mock_popen.returncode = 1
    logger.reset_mock()

    senza.create('yaml: yaml', '10', '42', ['param1', 'param2'])
    logger.error.assert_called_with('Failed to create stack.', extra={'command.output': '{"stream": "stdout"}'})
