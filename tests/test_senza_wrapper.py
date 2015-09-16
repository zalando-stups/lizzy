from unittest.mock import MagicMock, call, ANY, PropertyMock
import pytest
import logging

from lizzy.senza_wrapper import Senza


@pytest.fixture
def logger(monkeypatch):
    mock_log = MagicMock()
    monkeypatch.setattr('lizzy.senza_wrapper.logger', mock_log)
    return mock_log


@pytest.fixture
def popen(monkeypatch):
    mock_popen = MagicMock()
    mock_popen.return_value = mock_popen
    mock_popen.returncode = 0
    mock_popen.communicate.return_value = b'{"stream": "stdout"}', b'stderr'
    monkeypatch.setattr('subprocess.Popen', mock_popen)
    return mock_popen


def test_create(monkeypatch, logger, popen):
    mock_named_tempfile = MagicMock()
    mock_tempfile = MagicMock()
    mock_tempfile.name = 'filename'
    mock_named_tempfile.__enter__.return_value = mock_tempfile
    mock_named_tempfile.return_value = mock_named_tempfile
    monkeypatch.setattr('tempfile.NamedTemporaryFile', mock_named_tempfile)

    senza = Senza('region')
    senza.create('yaml: yaml', '10', '42', ['param1', 'param2'])

    mock_named_tempfile.assert_called_with()
    mock_tempfile.write.assert_called_with(b'yaml: yaml')

    popen.assert_called_with(
        ['senza', 'create', '--region', 'region', '--force', 'filename', '10', '42', 'param1', 'param2'],
        stdout=-1,
        stderr=-2)

    cmd = 'senza create --region region --force filename 10 42 param1 param2'
    logger.debug.assert_called_with('Executing senza.', extra={'command': cmd})
    assert not logger.error.called

    popen.returncode = 1
    logger.reset_mock()

    senza.create('yaml: yaml', '10', '42', ['param1', 'param2'])
    logger.error.assert_called_with('Failed to create stack.', extra={'command.output': '{"stream": "stdout"}'})


def test_domain(monkeypatch, logger, popen):
    senza = Senza('region')
    domains = senza.domains()

    cmd = 'senza domains --region region -o json'
    logger.debug.assert_called_with('Executing senza.', extra={'command': cmd})
    assert not logger.error.called
    assert not logger.exception.called

    popen.assert_called_with(
        ['senza', 'domains', '--region', 'region', '-o', 'json'],
        stdout=-1,
        stderr=-2)

    assert domains == {'stream': 'stdout'}

    logger.reset_mock()
    popen.reset_mock()

    popen.communicate.return_value = b'{"test": "domain2"}', b'stderr'
    domains = senza.domains('lizzy')

    cmd = 'senza domains --region region -o json lizzy'
    logger.debug.assert_called_with('Executing senza.', extra={'command': cmd})
    assert not logger.error.called
    assert not logger.exception.called

    popen.assert_called_with(['senza', 'domains', '--region', 'region', '-o', 'json', 'lizzy'], stdout=-1, stderr=-2)

    assert domains == {'test': 'domain2'}


def test_list(monkeypatch, logger, popen):
    popen.communicate.return_value = b'["item1", "item2"]', b'stderr'
    senza = Senza('region')
    list = senza.list()

    cmd = 'senza list --region region -o json'
    logger.debug.assert_called_with('Executing senza.', extra={'command': cmd})
    assert not logger.error.called
    assert not logger.exception.called

    popen.assert_called_with(['senza', 'list', '--region', 'region', '-o', 'json'], stdout=-1, stderr=-2)

    assert list == ["item1", "item2"]


def test_remove(monkeypatch, logger, popen):
    senza = Senza('region')
    senza.remove('lizzy', 'version')

    popen.assert_called_with(['senza', 'delete', '--region', 'region', 'lizzy', 'version'], stdout=-1, stderr=-2)

    cmd = 'senza delete --region region lizzy version'
    logger.debug.assert_called_with('Executing senza.', extra={'command': cmd})
    assert not logger.error.called
    assert not logger.exception.called

    popen.returncode = 1
    logger.reset_mock()

    senza.remove('lizzy', 'version')
    logger.error.assert_called_with('Failed to delete stack.', extra={'command.output': '{"stream": "stdout"}'})
