from unittest.mock import MagicMock

import pytest

from lizzy.apps.senza import Senza
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
    mock_named_tempfile = MagicMock()
    mock_tempfile = MagicMock()
    mock_tempfile.name = 'filename'
    mock_named_tempfile.__enter__.return_value = mock_tempfile
    mock_named_tempfile.return_value = mock_named_tempfile
    monkeypatch.setattr('tempfile.NamedTemporaryFile', mock_named_tempfile)

    senza = Senza('region')
    senza.logger = MagicMock()
    senza.create('yaml: yaml', '10', '42', ['param1', 'param2'], False)

    mock_named_tempfile.assert_called_with()
    mock_tempfile.write.assert_called_with(b'yaml: yaml')

    popen.assert_called_with(['senza', 'create',
                              '--region', 'region',
                              '--force', 'filename',
                              '10', '42', 'param1', 'param2'],
                             stdout=-1,
                             stderr=-2)

    cmd = 'senza create --region region --force filename 10 42 param1 param2'
    senza.logger.debug.assert_called_with('Executing %s.', 'senza', extra={'command': cmd})
    assert not senza.logger.error.called

    popen.reset_mock()
    senza.create('yaml: yaml', '10', '42', ['param1', 'param2'], True)

    mock_named_tempfile.assert_called_with()
    mock_tempfile.write.assert_called_with(b'yaml: yaml')

    popen.assert_called_with(['senza', 'create',
                              '--region', 'region',
                              '--force', '--disable-rollback', 'filename',
                              '10', '42', 'param1', 'param2'],
                             stdout=-1,
                             stderr=-2)

    popen.returncode = 1
    senza.logger.reset_mock()

    senza.create('yaml: yaml', '10', '42', ['param1', 'param2'], False)
    senza.logger.error.assert_called_with('Failed to create stack.', extra={'command.output': '{"stream": "stdout"}'})


def test_domain(monkeypatch, popen):
    senza = Senza('region')
    senza.logger = MagicMock()
    domains = senza.domains()

    cmd = 'senza domains --region region -o json'
    senza.logger.debug.assert_called_with('Executing %s.', 'senza', extra={'command': cmd})
    assert not senza.logger.error.called
    assert not senza.logger.exception.called

    popen.assert_called_with(['senza', 'domains', '--region', 'region', '-o', 'json'],
                             stdout=-1,
                             stderr=-1)

    assert domains == {'stream': 'stdout'}

    senza.logger.reset_mock()
    popen.reset_mock()

    popen.communicate.return_value = b'{"test": "domain2"}', b'stderr'
    domains = senza.domains('lizzy')

    cmd = 'senza domains --region region -o json lizzy'
    senza.logger.debug.assert_called_with('Executing %s.', 'senza', extra={'command': cmd})
    assert not senza.logger.error.called
    assert not senza.logger.exception.called

    popen.assert_called_with(['senza', 'domains', '--region', 'region', '-o', 'json', 'lizzy'], stdout=-1, stderr=-1)

    assert domains == {'test': 'domain2'}


def test_list(monkeypatch, popen):
    popen.communicate.return_value = b'["item1", "item2"]', b'stderr'
    senza = Senza('region')
    senza.logger = MagicMock()
    list = senza.list()

    cmd = 'senza list --region region -o json'
    senza.logger.debug.assert_called_with('Executing %s.', 'senza', extra={'command': cmd})
    assert not senza.logger.error.called
    assert not senza.logger.exception.called

    popen.assert_called_with(['senza', 'list', '--region', 'region', '-o', 'json'], stdout=-1, stderr=-1)

    assert list == ["item1", "item2"]

    # Test invalid json
    popen.communicate.return_value = b'"', b'stderr'
    with pytest.raises(ExecutionError):
        senza.list()


def test_remove(monkeypatch, popen):
    senza = Senza('region')
    senza.logger = MagicMock()
    senza.remove('lizzy', 'version')

    popen.assert_called_with(['senza', 'delete', '--region', 'region', 'lizzy', 'version'], stdout=-1, stderr=-2)

    cmd = 'senza delete --region region lizzy version'
    senza.logger.debug.assert_called_with('Executing %s.', 'senza', extra={'command': cmd})
    assert not senza.logger.error.called
    assert not senza.logger.exception.called

    popen.returncode = 1
    senza.logger.reset_mock()

    senza.remove('lizzy', 'version')
    senza.logger.error.assert_called_with('Failed to delete stack.', extra={'command.output': '{"stream": "stdout"}'})


def test_traffic(monkeypatch, popen):
    senza = Senza('region')
    senza.logger = MagicMock()
    traffic = senza.traffic('lizzy', 'version42', 25)

    cmd = 'senza traffic --region region -o json lizzy version42 25'
    senza.logger.debug.assert_called_with('Executing %s.', 'senza', extra={'command': cmd})
    assert not senza.logger.error.called
    assert not senza.logger.exception.called

    popen.assert_called_with(['senza', 'traffic', '--region', 'region', '-o', 'json', 'lizzy', 'version42', '25'],
                             stdout=-1,
                             stderr=-1)

    assert traffic == {'stream': 'stdout'}


def test_patch(monkeypatch, popen):
    senza = Senza('region')
    senza.logger = MagicMock()
    senza.patch('lizzy', 'version42', 'latest')

    cmd = 'senza patch --region region -o json lizzy version42 --image=latest'
    senza.logger.debug.assert_called_with('Executing %s.', 'senza', extra={'command': cmd})
    assert not senza.logger.error.called
    assert not senza.logger.exception.called


def test_exception():
    try:
        raise ExecutionError(20, '  Output         ')
    except ExecutionError as e:
        assert str(e) == '(20): Output'
