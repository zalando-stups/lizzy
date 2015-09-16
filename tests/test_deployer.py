from unittest.mock import MagicMock
import pytest

from lizzy.job.deployer import Deployer
from lizzy.models.stack import Stack

LIZZY_STACKS = {'lizzy': {'1': {},
                          '2': {},
                          '3': {},
                          '42': {},
                          'inprog': {},
                          'deployed': {}}}

CF_STACKS = {'lizzy': {'42': {'status': 'TEST'},
                       'inprog': {'status': 'CREATE_IN_PROGRESS'},
                       'deployed': {'status': 'CREATE_COMPLETE'}}}


@pytest.fixture
def logger(monkeypatch):
    mock_log = MagicMock()
    mock_log.return_value = mock_log
    monkeypatch.setattr('logging.getLogger', mock_log)
    return mock_log


def test_log_info():
    stack = Stack(stack_id='lizzy-42', creation_time='2015-09-16T09:48', keep_stacks=2, traffic=7, image_version='1.0',
                  senza_yaml='senza:yaml', stack_name='lizzy', stack_version='42', parameters=[], status='LIZZY:TEST')
    deployer = Deployer('region', LIZZY_STACKS, CF_STACKS, stack)
    assert deployer.log_info == {'cf_status': 'TEST',
                                 'lizzy.stack.id': 'lizzy-42',
                                 'lizzy.stack.name': 'lizzy',
                                 'lizzy.stack.traffic': 7}

    deployer_no_cf = Deployer('region', LIZZY_STACKS, {}, stack)
    assert deployer_no_cf.log_info == {'lizzy.stack.id': 'lizzy-42',
                                       'lizzy.stack.name': 'lizzy',
                                       'lizzy.stack.traffic': 7}


def test_new(monkeypatch, logger):
    mock_senza = MagicMock()
    mock_senza.return_value = mock_senza
    monkeypatch.setattr('lizzy.job.deployer.Senza', mock_senza)

    stack = Stack(stack_id='lizzy-42', creation_time='2015-09-16T09:48', keep_stacks=2, traffic=7, image_version='1.0',
                  senza_yaml='senza:yaml', stack_name='lizzy', stack_version='42', parameters=[], status='LIZZY:NEW')

    mock_senza.create.return_value = True
    deployer = Deployer('region', LIZZY_STACKS, CF_STACKS, stack)
    assert deployer.handle() == 'LIZZY:DEPLOYING'

    mock_senza.create.return_value = False
    deployer = Deployer('region', LIZZY_STACKS, CF_STACKS, stack)
    assert deployer.handle() == 'LIZZY:ERROR'


def test_deploying(monkeypatch, logger):
    mock_senza = MagicMock()
    mock_senza.return_value = mock_senza
    monkeypatch.setattr('lizzy.job.deployer.Senza', mock_senza)

    stack = Stack(stack_id='nonexisting-42', creation_time='2015-09-16T09:48', keep_stacks=2, traffic=7,
                  image_version='1.0', senza_yaml='senza:yaml', stack_name='nonexisting', stack_version='42',
                  parameters=[], status='LIZZY:DEPLOYING')

    deployer = Deployer('region', LIZZY_STACKS, CF_STACKS, stack)
    assert deployer.handle() == 'LIZZY:REMOVED'

    stack = Stack(stack_id='lizzy-inprog', creation_time='2015-09-16T09:48', keep_stacks=2, traffic=7,
                  image_version='1.0', senza_yaml='senza:yaml', stack_name='lizzy', stack_version='inprog',
                  parameters=[], status='LIZZY:DEPLOYING')

    deployer = Deployer('region', LIZZY_STACKS, CF_STACKS, stack)
    assert deployer.handle() == 'LIZZY:DEPLOYING'

    stack = Stack(stack_id='lizzy-deployed', creation_time='2015-09-16T09:48', keep_stacks=2, traffic=7,
                  image_version='1.0', senza_yaml='senza:yaml', stack_name='lizzy', stack_version='deployed',
                  parameters=[], status='LIZZY:DEPLOYING')

    deployer = Deployer('region', LIZZY_STACKS, CF_STACKS, stack)
    assert deployer.handle() == 'LIZZY:DEPLOYED'

    stack = Stack(stack_id='lizzy-42', creation_time='2015-09-16T09:48', keep_stacks=2, traffic=7,
                  image_version='1.0', senza_yaml='senza:yaml', stack_name='lizzy', stack_version='42',
                  parameters=[], status='LIZZY:DEPLOYING')

    deployer = Deployer('region', LIZZY_STACKS, CF_STACKS, stack)
    assert deployer.handle() == 'CF:TEST'


def test_deployed(monkeypatch, logger):
    mock_senza = MagicMock()
    mock_senza.domains.return_value = ['test.example']
    mock_senza.return_value = mock_senza
    monkeypatch.setattr('lizzy.job.deployer.Senza', mock_senza)

    stack = Stack(stack_id='nonexisting-42', creation_time='2015-09-16T09:48', keep_stacks=2, traffic=7,
                  image_version='1.0', senza_yaml='senza:yaml', stack_name='nonexisting', stack_version='42',
                  parameters=[], status='LIZZY:DEPLOYED')

    deployer = Deployer('region', LIZZY_STACKS, CF_STACKS, stack)
    assert deployer.handle() == 'LIZZY:REMOVED'

    stack = Stack(stack_id='lizzy-42', creation_time='2015-09-16T09:48', keep_stacks=2, traffic=7,
                  image_version='1.0', senza_yaml='senza:yaml', stack_name='lizzy', stack_version='42',
                  parameters=[], status='LIZZY:DEPLOYED')

    deployer = Deployer('region', LIZZY_STACKS, CF_STACKS, stack)
    assert deployer.handle() == 'CF:TEST'

    assert mock_senza.remove.call_count == 3
    mock_senza.traffic.assert_called_once_with(stack_name='lizzy', percentage=7, stack_version='42')


def test_lizzy_error(monkeypatch, logger):
    stack = Stack(stack_id='nonexisting-42', creation_time='2015-09-16T09:48', keep_stacks=2, traffic=7,
                  image_version='1.0', senza_yaml='senza:yaml', stack_name='nonexisting', stack_version='42',
                  parameters=[], status='LIZZY:ERROR')

    deployer = Deployer('region', LIZZY_STACKS, CF_STACKS, stack)
    assert deployer.handle() == 'LIZZY:ERROR'


def test_default(monkeypatch, logger):
    mock_senza = MagicMock()
    mock_senza.domains.return_value = ['test.example']
    mock_senza.return_value = mock_senza
    monkeypatch.setattr('lizzy.job.deployer.Senza', mock_senza)

    stack = Stack(stack_id='nonexisting-42', creation_time='2015-09-16T09:48', keep_stacks=2, traffic=7,
                  image_version='1.0', senza_yaml='senza:yaml', stack_name='nonexisting', stack_version='42',
                  parameters=[], status='CF:TESTING')

    deployer = Deployer('region', LIZZY_STACKS, CF_STACKS, stack)
    assert deployer.handle() == 'LIZZY:REMOVED'

    stack = Stack(stack_id='lizzy-42', creation_time='2015-09-16T09:48', keep_stacks=2, traffic=7,
                  image_version='1.0', senza_yaml='senza:yaml', stack_name='lizzy', stack_version='42',
                  parameters=[], status='LIZZY:TESTING')

    deployer = Deployer('region', LIZZY_STACKS, CF_STACKS, stack)
    assert deployer.handle() == 'CF:TEST'
