from datetime import datetime
from unittest.mock import MagicMock, call

import pytest
from factory import Factory, Sequence
from fixtures.boto import cf
from fixtures.senza_definitions import YAML1
from lizzy.deployer import InstantDeployer
from lizzy.exceptions import (AMIImageNotUpdated, SenzaDomainsError,
                              SenzaPatchError, SenzaTrafficError,
                              TrafficNotUpdated)
from lizzy.job.deployer import Deployer
from lizzy.models.stack import REMOVED_STACK, Stack

CF_STACKS = {'lizzy': {'42': {'status': 'TEST'},
                       'inprog': {'status': 'CREATE_IN_PROGRESS'},
                       'deployed': {'status': 'CREATE_COMPLETE'}}}


class StackFactory(Factory):
    class Meta:
        model = Stack

    stack_name = Sequence(lambda x: 'stack_{}'.format(x))
    creation_time = '2015-09-16T09:48'
    image_version = Sequence(lambda x: 'version_{}'.format(x))
    stack_version = None
    traffic = 100
    keep_stacks = 2
    senza_yaml = YAML1
    status = 'LIZZY:TEST'
    image_version = '1.0'


LIZZY_STACKS = {
    'lizzy': {
        '1': StackFactory(stack_name='lizzy-1',
                          stack_version='1',
                          creation_time=datetime(2016, 3, 10, 12, 30)),

        '2': StackFactory(stack_name='lizzy-2',
                          stack_version='2',
                          creation_time=datetime(2016, 3, 12, 12, 30)),

        '3': StackFactory(stack_name='lizzy-3',
                          stack_version='3',
                          creation_time=datetime(2016, 3, 13, 12, 30)),

        '9': StackFactory(stack_name='lizzy-9',
                          stack_version='9',
                          creation_time=datetime(2016, 3, 19, 12, 30)),

        '42': StackFactory(stack_name='lizzy-42',
                           stack_version='42',
                           creation_time=datetime(2016, 3, 27, 12, 30)),

        'inprog': StackFactory(stack_name='lizzy-inprog',
                               stack_version='inprog',
                               creation_time=datetime(2016, 3, 20, 12, 30)),

        'deployed': StackFactory(stack_name='lizzy-deployed',
                                 stack_version='deployed',
                                 creation_time=datetime(2016, 3, 21, 12, 30))
    }
}


@pytest.fixture
def logger(monkeypatch):
    mock_log = MagicMock()
    mock_log.return_value = mock_log
    monkeypatch.setattr('logging.getLogger', mock_log)
    return mock_log


def test_log_info():
    stack = Stack(stack_id='lizzy-42', creation_time='2015-09-16T09:48', keep_stacks=2, traffic=7, image_version='1.0',
                  senza_yaml=YAML1, stack_name='lizzy', stack_version='42', status='LIZZY:TEST')
    deployer = Deployer('region', LIZZY_STACKS, CF_STACKS, stack)
    assert deployer.log_info == {'cf_status': 'TEST',
                                 'lizzy.stack.id': 'lizzy-42',
                                 'lizzy.stack.name': 'lizzy',
                                 'lizzy.stack.traffic': 7}

    deployer_no_cf = Deployer('region', LIZZY_STACKS, {}, stack)
    assert deployer_no_cf.log_info == {'lizzy.stack.id': 'lizzy-42',
                                       'lizzy.stack.name': 'lizzy',
                                       'lizzy.stack.traffic': 7}


def test_deploying(monkeypatch, logger):
    mock_senza = MagicMock()
    mock_senza.return_value = mock_senza
    monkeypatch.setattr('lizzy.job.deployer.Senza', mock_senza)

    stack = Stack(stack_id='nonexisting-42', creation_time='2015-09-16T09:48', keep_stacks=2, traffic=7,
                  image_version='1.0', senza_yaml=YAML1, stack_name='nonexisting', stack_version='42',
                  status='LIZZY:DEPLOYING')

    deployer = Deployer('region', LIZZY_STACKS, CF_STACKS, stack)
    assert deployer.handle() is REMOVED_STACK

    stack = Stack(stack_id='lizzy-inprog', creation_time='2015-09-16T09:48', keep_stacks=2, traffic=7,
                  image_version='1.0', senza_yaml=YAML1, stack_name='lizzy', stack_version='inprog',
                  status='LIZZY:DEPLOYING')

    deployer = Deployer('region', LIZZY_STACKS, CF_STACKS, stack)
    assert deployer.handle() == 'CF:CREATE_IN_PROGRESS'

    stack = Stack(stack_id='lizzy-deployed', creation_time='2015-09-16T09:48', keep_stacks=2, traffic=7,
                  image_version='1.0', senza_yaml=YAML1, stack_name='lizzy', stack_version='deployed',
                  status='LIZZY:DEPLOYING')

    deployer = Deployer('region', LIZZY_STACKS, CF_STACKS, stack)
    assert deployer.handle() == 'CF:CREATE_COMPLETE'

    stack = Stack(stack_id='lizzy-42', creation_time='2015-09-16T09:48', keep_stacks=2, traffic=7,
                  image_version='1.0', senza_yaml=YAML1, stack_name='lizzy', stack_version='42',
                  status='LIZZY:DEPLOYING')

    deployer = Deployer('region', LIZZY_STACKS, CF_STACKS, stack)
    assert deployer.handle() == 'CF:TEST'


def test_deploying_create_in_progress(monkeypatch, logger):
    mock_senza = MagicMock()
    mock_senza.return_value = mock_senza
    monkeypatch.setattr('lizzy.job.deployer.Senza', mock_senza)

    stack = Stack(stack_id='nonexisting-42', creation_time='2015-09-16T09:48', keep_stacks=2, traffic=7,
                  image_version='1.0', senza_yaml=YAML1, stack_name='nonexisting', stack_version='42',
                  status='CF:CREATE_IN_PROGRESS')

    deployer = Deployer('region', LIZZY_STACKS, CF_STACKS, stack)
    assert deployer.handle() is REMOVED_STACK

    stack = Stack(stack_id='lizzy-inprog', creation_time='2015-09-16T09:48', keep_stacks=2, traffic=7,
                  image_version='1.0', senza_yaml=YAML1, stack_name='lizzy', stack_version='inprog',
                  status='CF:CREATE_IN_PROGRESS')

    deployer = Deployer('region', LIZZY_STACKS, CF_STACKS, stack)
    assert deployer.handle() == 'CF:CREATE_IN_PROGRESS'

    stack = Stack(stack_id='lizzy-deployed', creation_time='2015-09-16T09:48', keep_stacks=2, traffic=7,
                  image_version='1.0', senza_yaml=YAML1, stack_name='lizzy', stack_version='deployed',
                  status='CF:CREATE_IN_PROGRESS')

    deployer = Deployer('region', LIZZY_STACKS, CF_STACKS, stack)
    assert deployer.handle() == 'CF:CREATE_COMPLETE'

    stack = Stack(stack_id='lizzy-42', creation_time='2015-09-16T09:48', keep_stacks=2, traffic=7,
                  image_version='1.0', senza_yaml=YAML1, stack_name='lizzy', stack_version='42',
                  status='CF:CREATE_IN_PROGRESS')

    deployer = Deployer('region', LIZZY_STACKS, CF_STACKS, stack)
    assert deployer.handle() == 'CF:TEST'


def test_deployed(monkeypatch, logger, cf):  # NOQA
    mock_senza = MagicMock()
    mock_senza.domains.return_value = ['test.example']
    mock_senza.return_value = mock_senza
    monkeypatch.setattr('lizzy.job.deployer.Senza', mock_senza)

    stack = StackFactory(stack_id='nonexisting-42',
                         creation_time='2015-09-27T09:48', keep_stacks=2,
                         stack_version='42', traffic=7,
                         status='LIZZY:DEPLOYED')

    deployer = Deployer('region', LIZZY_STACKS, CF_STACKS, stack)
    assert deployer.handle() is REMOVED_STACK

    stack = StackFactory(stack_id='lizzy-42', creation_time='2015-09-27T09:48',
                         keep_stacks=2, stack_name='lizzy', traffic=7,
                         stack_version='42', status='LIZZY:DEPLOYED')

    deployer = Deployer('region', LIZZY_STACKS, CF_STACKS, stack)
    assert deployer.handle() == 'CF:TEST'

    # If stack has traffic of 0, do not call senza.traffic command
    mock_senza.reset_mock()
    mock_senza.domains.return_value = ['test.example']
    mock_senza.return_value = mock_senza

    stack = StackFactory.create(stack_name='lizzy',
                                stack_version='42',
                                traffic=0,
                                status='LIZZY:DEPLOYED')

    deployer = Deployer('region', LIZZY_STACKS, CF_STACKS, stack)
    assert deployer.handle() == 'CF:TEST'
    mock_senza.traffic.assert_not_called()


def test_default(monkeypatch, logger):
    mock_senza = MagicMock()
    mock_senza.domains.return_value = ['test.example']
    mock_senza.return_value = mock_senza
    monkeypatch.setattr('lizzy.job.deployer.Senza', mock_senza)

    stack = Stack(stack_id='nonexisting-42', creation_time='2015-09-16T09:48', keep_stacks=2, traffic=7,
                  image_version='1.0', senza_yaml=YAML1, stack_name='nonexisting', stack_version='42',
                  status='CF:TESTING')

    deployer = Deployer('region', LIZZY_STACKS, CF_STACKS, stack)
    assert deployer.handle() is REMOVED_STACK

    stack = Stack(stack_id='lizzy-42', creation_time='2015-09-16T09:48', keep_stacks=2, traffic=7,
                  image_version='1.0', senza_yaml=YAML1, stack_name='lizzy', stack_version='42',
                  status='LIZZY:TESTING')

    deployer = Deployer('region', LIZZY_STACKS, CF_STACKS, stack)
    assert deployer.handle() == 'CF:TEST'


def test_delete(monkeypatch, logger):
    mock_senza = MagicMock()
    mock_senza.traffic.return_value = ['test.example']
    mock_senza.return_value = mock_senza
    monkeypatch.setattr('lizzy.deployer.Senza', mock_senza)

    stack = Stack(stack_id='lizzy-42', creation_time='2015-09-16T09:48',
                  keep_stacks=2, traffic=47,
                  image_version='1.0', senza_yaml=YAML1, stack_name='lizzy',
                  stack_version='42',
                  status='LIZZY:CHANGE')

    instant_deployer = InstantDeployer(stack)
    instant_deployer.delete_stack()

    mock_senza.remove.assert_called_once_with('lizzy', '42')


def test_update_ami_image(monkeypatch):
    mock_senza = MagicMock()
    mock_senza.domains.return_value = ['test.example']
    mock_senza.return_value = mock_senza
    monkeypatch.setattr('lizzy.deployer.Senza', mock_senza)

    stack = Stack(stack_id='lizzy-42', creation_time='2015-09-16T09:48', keep_stacks=2, traffic=47,
                  image_version='1.0', senza_yaml=YAML1, stack_name='lizzy', stack_version='42',
                  status='LIZZY:NEW')

    # everything works as expected
    instant_deployer = InstantDeployer(stack)
    instant_deployer.update_ami_image('latest')

    mock_senza.patch.assert_called_once_with('lizzy', '42', 'latest')
    mock_senza.respawn_instances.assert_called_once_with('lizzy', '42')

    # while running the one of the senza commands an error occour
    mock_senza.patch.side_effect = SenzaPatchError('', '')

    with pytest.raises(AMIImageNotUpdated):
        instant_deployer.update_ami_image('latest')


def test_change_traffic(monkeypatch, logger):
    mock_senza = MagicMock()
    mock_senza.traffic.return_value = ['test.example']
    mock_senza.return_value = mock_senza
    monkeypatch.setattr('lizzy.deployer.Senza', mock_senza)

    stack = Stack(stack_id='lizzy-42', creation_time='2015-09-16T09:48',
                  keep_stacks=2, traffic=47,
                  image_version='1.0', senza_yaml=YAML1, stack_name='lizzy',
                  stack_version='42',
                  status='LIZZY:CHANGE')

    instant_deployer = InstantDeployer(stack)
    instant_deployer.change_traffic(100)

    mock_senza.traffic.assert_called_once_with(percentage=100,
                                               stack_name='lizzy',
                                               stack_version='42')

    # while running the one of the senza commands an error occurs
    mock_senza.traffic.side_effect = SenzaDomainsError('', '')

    with pytest.raises(TrafficNotUpdated):
        instant_deployer.change_traffic(100)

    mock_senza.traffic.side_effect = SenzaTrafficError('', '')

    with pytest.raises(TrafficNotUpdated):
        instant_deployer.change_traffic(100)

    mock_senza.traffic.side_effect = None
    mock_senza.domains.return_value = []
    with pytest.raises(TrafficNotUpdated):
        instant_deployer.change_traffic(100)
