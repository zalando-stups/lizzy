from unittest.mock import MagicMock
import pytest

from lizzy.job.deployer import Deployer
from lizzy.models.stack import Stack
from lizzy.deployer import InstantDeployer
from lizzy.exceptions import SenzaPatchError, AIMImageNotUpdated

LIZZY_STACKS = {'lizzy': {'1': {},
                          '2': {},
                          '3': {},
                          '42': {},
                          'inprog': {},
                          'deployed': {}}}

CF_STACKS = {'lizzy': {'42': {'status': 'TEST'},
                       'inprog': {'status': 'CREATE_IN_PROGRESS'},
                       'deployed': {'status': 'CREATE_COMPLETE'}}}

YAML1 = """
SenzaInfo:
  Parameters:
  - ImageVersion: {Description: Docker image version of lizzy.}
  StackName: lizzy
Test: lizzy:{{Arguments.ImageVersion}}
SenzaComponents:
- Configuration: {Type: 'Senza::StupsAutoConfiguration'}
- AppServer:
    AssociatePublicIpAddress: false
    ElasticLoadBalancer: AppLoadBalancer
    IamRoles: [app-lizzy-bus]
    InstanceType: t2.micro
    SecurityGroups: [app-lizzy-bus]
    TaupageConfig:
      application_version: '{{Arguments.ImageVersion}}'
      health_check_path: /api/swagger.json
      ports: {8080: 8080}
      runtime: Docker
      source: lizzy:{{Arguments.ImageVersion}}
    Type: Senza::TaupageAutoScalingGroup
"""

YAML2 = """
SenzaInfo:
  Parameters:
  - ImageVersion: {Description: Docker image version of lizzy.}
  - Test1:  {Description: test}
  - Test2:  {Description: test}
  StackName: lizzy
Test: lizzy:{{Arguments.ImageVersion}}
Test2: test-{{Arguments.Test1}}
"""


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
    assert deployer.handle() == 'LIZZY:REMOVED'

    stack = Stack(stack_id='lizzy-inprog', creation_time='2015-09-16T09:48', keep_stacks=2, traffic=7,
                  image_version='1.0', senza_yaml=YAML1, stack_name='lizzy', stack_version='inprog',
                  status='LIZZY:DEPLOYING')

    deployer = Deployer('region', LIZZY_STACKS, CF_STACKS, stack)
    assert deployer.handle() == 'LIZZY:DEPLOYING'

    stack = Stack(stack_id='lizzy-deployed', creation_time='2015-09-16T09:48', keep_stacks=2, traffic=7,
                  image_version='1.0', senza_yaml=YAML1, stack_name='lizzy', stack_version='deployed',
                  status='LIZZY:DEPLOYING')

    deployer = Deployer('region', LIZZY_STACKS, CF_STACKS, stack)
    assert deployer.handle() == 'LIZZY:DEPLOYED'

    stack = Stack(stack_id='lizzy-42', creation_time='2015-09-16T09:48', keep_stacks=2, traffic=7,
                  image_version='1.0', senza_yaml=YAML1, stack_name='lizzy', stack_version='42',
                  status='LIZZY:DEPLOYING')

    deployer = Deployer('region', LIZZY_STACKS, CF_STACKS, stack)
    assert deployer.handle() == 'CF:TEST'


def test_deployed(monkeypatch, logger):
    mock_senza = MagicMock()
    mock_senza.domains.return_value = ['test.example']
    mock_senza.return_value = mock_senza
    monkeypatch.setattr('lizzy.job.deployer.Senza', mock_senza)

    stack = Stack(stack_id='nonexisting-42', creation_time='2015-09-16T09:48', keep_stacks=2, traffic=7,
                  image_version='1.0', senza_yaml=YAML1, stack_name='nonexisting', stack_version='42',
                  status='LIZZY:DEPLOYED')

    deployer = Deployer('region', LIZZY_STACKS, CF_STACKS, stack)
    assert deployer.handle() == 'LIZZY:REMOVED'

    stack = Stack(stack_id='lizzy-42', creation_time='2015-09-16T09:48', keep_stacks=2, traffic=7,
                  image_version='1.0', senza_yaml=YAML1, stack_name='lizzy', stack_version='42',
                  status='LIZZY:DEPLOYED')

    deployer = Deployer('region', LIZZY_STACKS, CF_STACKS, stack)
    assert deployer.handle() == 'CF:TEST'

    assert mock_senza.remove.call_count == 3
    mock_senza.traffic.assert_called_once_with(stack_name='lizzy', percentage=7, stack_version='42')


def test_lizzy_error(monkeypatch, logger):
    stack = Stack(stack_id='nonexisting-42', creation_time='2015-09-16T09:48', keep_stacks=2, traffic=7,
                  image_version='1.0', senza_yaml=YAML1, stack_name='nonexisting', stack_version='42',
                  status='LIZZY:ERROR')

    deployer = Deployer('region', LIZZY_STACKS, CF_STACKS, stack)
    assert deployer.handle() == 'LIZZY:ERROR'


def test_default(monkeypatch, logger):
    mock_senza = MagicMock()
    mock_senza.domains.return_value = ['test.example']
    mock_senza.return_value = mock_senza
    monkeypatch.setattr('lizzy.job.deployer.Senza', mock_senza)

    stack = Stack(stack_id='nonexisting-42', creation_time='2015-09-16T09:48', keep_stacks=2, traffic=7,
                  image_version='1.0', senza_yaml=YAML1, stack_name='nonexisting', stack_version='42',
                  status='CF:TESTING')

    deployer = Deployer('region', LIZZY_STACKS, CF_STACKS, stack)
    assert deployer.handle() == 'LIZZY:REMOVED'

    stack = Stack(stack_id='lizzy-42', creation_time='2015-09-16T09:48', keep_stacks=2, traffic=7,
                  image_version='1.0', senza_yaml=YAML1, stack_name='lizzy', stack_version='42',
                  status='LIZZY:TESTING')

    deployer = Deployer('region', LIZZY_STACKS, CF_STACKS, stack)
    assert deployer.handle() == 'CF:TEST'


def test_delete(monkeypatch, logger):
    mock_senza = MagicMock()
    mock_senza.return_value = mock_senza
    monkeypatch.setattr('lizzy.job.deployer.Senza', mock_senza)

    stack = Stack(stack_id='lizzy-42', creation_time='2015-09-16T09:48', keep_stacks=2, traffic=7,
                  image_version='1.0', senza_yaml=YAML1, stack_name='lizzy', stack_version='42',
                  status='LIZZY:DELETE')

    deployer = Deployer('region', LIZZY_STACKS, CF_STACKS, stack)
    assert deployer.handle() == 'CF:TEST'

    mock_senza.remove.assert_called_once_with('lizzy', '42')


def test_change(monkeypatch, logger):
    mock_senza = MagicMock()
    mock_senza.domains.return_value = ['test.example']
    mock_senza.return_value = mock_senza
    monkeypatch.setattr('lizzy.job.deployer.Senza', mock_senza)

    stack = Stack(stack_id='lizzy-42', creation_time='2015-09-16T09:48', keep_stacks=2, traffic=47,
                  image_version='1.0', senza_yaml=YAML1, stack_name='lizzy', stack_version='42',
                  status='LIZZY:CHANGE')

    deployer = Deployer('region', LIZZY_STACKS, CF_STACKS, stack)
    assert deployer.handle() == 'CF:TEST'

    mock_senza.traffic.assert_called_once_with(percentage=47, stack_name='lizzy', stack_version='42')


def test_update_aim_image(monkeypatch):
    mock_senza = MagicMock()
    mock_senza.domains.return_value = ['test.example']
    mock_senza.return_value = mock_senza
    monkeypatch.setattr('lizzy.deployer.Senza', mock_senza)

    stack = Stack(stack_id='lizzy-42', creation_time='2015-09-16T09:48', keep_stacks=2, traffic=47,
                  image_version='1.0', senza_yaml=YAML1, stack_name='lizzy', stack_version='42',
                  status='LIZZY:NEW')

    # everything works as expected
    instant_deployer = InstantDeployer(stack)
    instant_deployer.update_aim_image('latest')

    mock_senza.patch.assert_called_once_with('lizzy', '42', 'latest')
    mock_senza.respawn_instances.assert_called_once_with('lizzy', '42')

    # while running the one of the senza commands an error occour
    mock_senza.patch.side_effect = SenzaPatchError('', '')

    with pytest.raises(AIMImageNotUpdated):
        instant_deployer.update_aim_image('latest')
