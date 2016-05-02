import json
import os
from unittest.mock import ANY, MagicMock

import lizzy.api
import pytest
import requests
from fixtures.cloud_formation import (BAD_CF_DEFINITION,
                                      BAD_CF_MISSING_TAUPAGE_AUTOSCALING_GROUP,
                                      GOOD_CF_DEFINITION,
                                      GOOD_CF_DEFINITION_WITH_UNUSUAL_AUTOSCALING_RESOURCE)
from fixtures.senza import mock_senza
from lizzy.exceptions import (AMIImageNotUpdated, ObjectNotFound,
                              SenzaRenderError, TrafficNotUpdated,
                              ExecutionError, SenzaDomainsError)
from lizzy.models.stack import Stack
from lizzy.service import setup_webapp
from lizzy.version import VERSION

CURRENT_VERSION = VERSION

GOOD_HEADERS = {'Authorization': 'Bearer 100', 'Content-type': 'application/json'}

STACKS = {'stack-1': {'stack_id': None,
                      'creation_time': None,
                      'keep_stacks': 1,
                      'traffic': 100,
                      'image_version': 'version',
                      'ami_image': 'latest',
                      'senza_yaml': 'yaml',
                      'stack_name': 'stackno1',
                      'stack_version': 'v1',
                      'status': 'LIZZY:NEW', }}


class FakeConfig:
    def __init__(self):
        self.deployer_scope = 'myscope'
        self.token_url = 'https://ouath.example/access_token'
        self.port = 8080


class FakeResponse:
    def __init__(self, status_code: int, text: str):
        self.status_code = status_code
        self.text = text
        self.ok = status_code == 200

    def json(self):
        return json.loads(self.text)


class FakeRequest:
    def __init__(self, status_code: int, text: str):
        self.status_code = status_code
        self.text = text
        self.ok = status_code == 200

    def json(self):
        return json.loads(self.text)


class FakeStack(Stack):
    # TODO Implement some stacks

    last_save = {}

    @classmethod
    def all(cls):
        return []

    def delete(self):
        pass

    def save(self):
        FakeStack.last_save = vars(self)


@pytest.fixture
def app(monkeypatch):
    os.environ['TOKENINFO_URL'] = 'https://ouath.example/token_info'
    app = setup_webapp(FakeConfig())
    app_client = app.app.test_client()

    monkeypatch.setattr(lizzy.api, 'Stack', FakeStack)

    return app_client


@pytest.fixture(autouse=True)
def oauth_requests(monkeypatch: '_pytest.monkeypatch.monkeypatch'):
    class Session(requests.Session):
        def get(self, url: str, params: dict=None, timeout=0):
            params = params or {}
            if url == "https://ouath.example/token_info":
                token = params['access_token']
                if token == "100":
                    return FakeResponse(200, '{"scope": ["myscope"], "uid": "test_user"}')
                if token == "200":
                    return FakeResponse(200, '{"scope": ["wrongscope"], , "uid": "test_user"}')
                if token == "300":
                    return FakeResponse(404, '')
            return url

    monkeypatch.setattr('connexion.decorators.security.session', Session())


def test_security(app, oauth_requests, mock_senza):
    get_swagger = app.get('/api/swagger.json')  # type:flask.Response
    assert get_swagger.status_code == 200

    get_stacks_no_auth = app.get('/api/stacks')  # type:flask.Response
    assert get_stacks_no_auth.status_code == 401

    get_stacks = app.get('/api/stacks', headers=GOOD_HEADERS)
    assert get_stacks.status_code == 200
    assert get_stacks.headers['X-Lizzy-Version'] == CURRENT_VERSION

    inexistent_url = app.get('/api/does-not-exist', headers=GOOD_HEADERS)
    assert inexistent_url.status_code == 403

    invalid_access = app.get('/api/does-not-exist')
    assert invalid_access.status_code == 401

    invalid_access = app.get('/random-access-that-does-not-exist-outside-of-api')
    assert invalid_access.status_code == 401


def test_security_allowed_user_pattern(monkeypatch, mock_senza):
    os.environ['TOKENINFO_URL'] = 'https://ouath.example/token_info'

    class AllowedOtherUsersConfig(FakeConfig):
        def __init__(self):
            super().__init__()
            self.allowed_users = None
            self.allowed_user_pattern = '^test_.*'

    app = setup_webapp(AllowedOtherUsersConfig())
    app_client = app.app.test_client()

    monkeypatch.setattr(lizzy.security, 'Configuration', AllowedOtherUsersConfig)
    monkeypatch.setattr(lizzy.api, 'Stack', FakeStack)

    stacks_response = app_client.get('/api/stacks', headers=GOOD_HEADERS)
    assert stacks_response.status_code == 200


def test_security_now_allowed_user_pattern(monkeypatch):
    os.environ['TOKENINFO_URL'] = 'https://ouath.example/token_info'

    class AllowedOtherUsersConfig(FakeConfig):
        def __init__(self):
            super().__init__()
            self.allowed_users = None
            self.allowed_user_pattern = '^somethingelse_.*'

    app = setup_webapp(AllowedOtherUsersConfig())
    app_client = app.app.test_client()

    monkeypatch.setattr(lizzy.security, 'Configuration', AllowedOtherUsersConfig)
    monkeypatch.setattr(lizzy.api, 'Stack', FakeStack)

    stacks_response = app_client.get('/api/stacks', headers=GOOD_HEADERS)
    assert stacks_response.status_code == 403


def test_empty_new_stack(monkeypatch, app, oauth_requests):
    data = {}
    request = app.post('/api/stacks', headers=GOOD_HEADERS, data=json.dumps(data))  # type: flask.Response
    assert request.status_code == 400
    response = json.loads(request.data.decode())
    assert response['title'] == 'Bad Request'


def test_bad_senza_yaml(app, oauth_requests, monkeypatch):
    data = {'keep_stacks': 0,
            'stack_version': 1,
            'new_traffic': 100,
            'image_version': '1.0',
            'stack_version': '40',
            'senza_yaml': 'key: value'}

    mock_senza = MagicMock()
    mock_senza.return_value = mock_senza
    monkeypatch.setattr('lizzy.api.Senza', mock_senza)
    mock_senza.render_definition.side_effect = SenzaRenderError("Some error", "output error")

    request = app.post('/api/stacks', headers=GOOD_HEADERS, data=json.dumps(data))  # type: flask.Response
    assert request.status_code == 400
    response = json.loads(request.data.decode())
    assert response['title'] == 'Invalid senza yaml'
    assert request.headers['X-Lizzy-Version'] == CURRENT_VERSION

    mock_senza = MagicMock()
    mock_senza.return_value = mock_senza
    monkeypatch.setattr('lizzy.api.Senza', mock_senza)
    mock_senza.render_definition.return_value = BAD_CF_DEFINITION

    data['senza_yaml'] = '[]'
    request = app.post('/api/stacks', headers=GOOD_HEADERS, data=json.dumps(data))  # type: flask.Response
    assert request.status_code == 400
    response = json.loads(request.data.decode())
    assert response['title'] == 'Invalid senza yaml'
    assert response['detail'] == "Missing property in senza yaml: 'Fn::Base64'"
    assert request.headers['X-Lizzy-Version'] == CURRENT_VERSION


def test_new_stack(monkeypatch, app, mock_senza, oauth_requests):
    data = {'keep_stacks': 0,
            'new_traffic': 100,
            'image_version': '1.0',
            'stack_version': '1',
            'senza_yaml': 'SenzaInfo:\n  StackName: abc'}

    mock_kio = MagicMock()
    mock_kio.return_value = mock_kio
    monkeypatch.setattr('lizzy.api.Kio', mock_kio)
    mock_senza.render_definition.return_value = GOOD_CF_DEFINITION

    mock_senza.create.return_value = True
    request = app.post('/api/stacks',
                       headers=GOOD_HEADERS,
                       data=json.dumps(data))  # type: flask.Response
    mock_kio.assert_not_called()
    mock_senza.assert_called_with('eu-west-1')
    mock_senza.create.assert_called_with('SenzaInfo:\n  StackName: abc',
                                         ANY, '1.0', [], False,
                                         {'LizzyTargetTraffic': 100,
                                          'LizzyKeepStacks': 0})
    assert request.status_code == 201
    assert request.headers['X-Lizzy-Version'] == CURRENT_VERSION
    response = json.loads(request.get_data().decode())
    assert len(response) == 5
    assert response['creation_time'] == '2016-04-14T11:59:27+0000'


    data = {'keep_stacks': 0,
            'new_traffic': 100,
            'image_version': '1.0',
            'senza_yaml': 'SenzaInfo:\n  StackName: abc',
            'stack_version': '2b',
            'parameters': ['abc', 'def']}

    request = app.post('/api/stacks', headers=GOOD_HEADERS, data=json.dumps(data))  # type: flask.Response
    mock_kio.assert_not_called()
    mock_senza.assert_called_with('eu-west-1')
    mock_senza.create.assert_called_with('SenzaInfo:\n  StackName: abc',
                                         '2b', '1.0', ['abc', 'def'], False,
                                         {'LizzyTargetTraffic': 100,
                                          'LizzyKeepStacks': 0})
    assert request.status_code == 201
    assert request.headers['X-Lizzy-Version'] == CURRENT_VERSION

    data = {'keep_stacks': 0,
            'new_traffic': 100,
            'image_version': '1.0',
            'stack_version': '42',
            'senza_yaml': 'SenzaInfo:\n  StackName: abc',
            'parameters': ['abc', 'def'],
            'application_version': '42'}
    mock_senza.reset_mock()
    mock_senza.render_definition.return_value = GOOD_CF_DEFINITION
    mock_kio.versions_create.return_value = True
    request = app.post('/api/stacks', headers=GOOD_HEADERS, data=json.dumps(data))  # type: flask.Response
    mock_senza.assert_called_with('eu-west-1')
    mock_senza.create.assert_called_with('SenzaInfo:\n  StackName: abc',
                                         '42', '1.0', ['abc', 'def'], False,
                                         {'LizzyKeepStacks': 0,
                                          'LizzyTargetTraffic': 100})
    mock_kio.assert_called_with()
    mock_kio.versions_create.assert_called_once_with(application_id='abc',
                                                     artifact='pierone.example.com/lizzy/lizzy:12',
                                                     version='42')
    assert request.status_code == 201
    assert request.headers['X-Lizzy-Version'] == CURRENT_VERSION
    request_data = json.loads(request.data.decode())
    assert request_data == {'creation_time': '2016-04-14T11:59:27+0000',
                           'description': 'Lizzy Bus (ImageVersion: 257)',
                           'stack_name': 'lizzy-bus',
                           'status': 'CREATE_COMPLETE',
                           'version': '257'}


    mock_kio.reset_mock()
    mock_senza.reset_mock()
    mock_senza.render_definition.return_value = GOOD_CF_DEFINITION
    data = {'keep_stacks': 0,
            'new_traffic': 100,
            'image_version': '1.0',
            'stack_version': '7',
            'senza_yaml': 'SenzaInfo:\n  StackName: abc',
            'parameters': ['abc', 'def'],
            'application_version': '42',
            'disable_rollback': True}

    mock_kio.versions_create.return_value = True
    request = app.post('/api/stacks', headers=GOOD_HEADERS,
                       data=json.dumps(data))  # type: flask.Response
    mock_senza.assert_called_with('eu-west-1')
    mock_senza.create.assert_called_with('SenzaInfo:\n  StackName: abc',
                                         '7', '1.0',
                                         ['abc', 'def'],
                                         True,
                                         {'LizzyKeepStacks': 0,
                                          'LizzyTargetTraffic': 100})
    mock_kio.assert_called_with()
    mock_kio.versions_create.assert_called_once_with(application_id='abc',
                                                     artifact='pierone.example.com/lizzy/lizzy:12',
                                                     version='42')
    assert request.status_code == 201
    assert request.headers['X-Lizzy-Version'] == CURRENT_VERSION
    request_data = json.loads(request.data.decode())
    assert request_data == {'creation_time': '2016-04-14T11:59:27+0000',
                            'description': 'Lizzy Bus (ImageVersion: 257)',
                            'stack_name': 'lizzy-bus',
                            'status': 'CREATE_COMPLETE',
                            'version': '257'}

    # kio version creation doesn't affect the rest of the process
    mock_kio.versions_create.reset_mock()
    mock_kio.versions_create.return_value = False
    request = app.post('/api/stacks',
                       headers=GOOD_HEADERS,
                       data=json.dumps(data))  # type: flask.Response
    mock_kio.assert_called_with()
    mock_kio.versions_create.assert_called_once_with(application_id='abc',
                                                     artifact='pierone.example.com/lizzy/lizzy:12',
                                                     version='42')
    assert request.status_code == 201
    assert request.headers['X-Lizzy-Version'] == CURRENT_VERSION
    request_data = json.loads(request.data.decode())
    assert request_data == {'creation_time': '2016-04-14T11:59:27+0000',
                            'description': 'Lizzy Bus (ImageVersion: 257)',
                            'stack_name': 'lizzy-bus',
                            'status': 'CREATE_COMPLETE',
                            'version': '257'}

    mock_senza.create.return_value = False
    request = app.post('/api/stacks',
                       headers=GOOD_HEADERS,
                       data=json.dumps(data))  # type: flask.Response
    assert request.status_code == 400

    # Test creating stack with parameters to senza
    mock_senza.reset_mock()
    mock_senza.create.return_value = True
    mock_senza.render_definition.return_value = GOOD_CF_DEFINITION
    mock_kio.versions_create.reset_mock()
    mock_kio.versions_create.return_value = True
    data = {'keep_stacks': 0,
            'new_traffic': 100,
            'image_version': '1.0',
            'stack_version': '43',
            'senza_yaml': 'SenzaInfo:\n  StackName: abc',
            'parameters': ['MintBucket=bk-bucket', 'ImageVersion=28']}

    request = app.post('/api/stacks',
                       headers=GOOD_HEADERS,
                       data=json.dumps(data))
    mock_senza.create.assert_called_with('SenzaInfo:\n  StackName: abc', '43',
                                         '1.0', ['MintBucket=bk-bucket',
                                                 'ImageVersion=28'], False,
                                         {'LizzyKeepStacks': 0,
                                          'LizzyTargetTraffic': 100})
    request_data = json.loads(request.data.decode())
    assert request_data == {'creation_time': '2016-04-14T11:59:27+0000',
                            'description': 'Lizzy Bus (ImageVersion: 257)',
                            'stack_name': 'lizzy-bus',
                            'status': 'CREATE_COMPLETE',
                            'version': '257'}

    # unusual launch configuration name (usually is AppServer)
    mock_kio.reset_mock()
    mock_senza.reset_mock()
    mock_senza.render_definition.return_value = GOOD_CF_DEFINITION_WITH_UNUSUAL_AUTOSCALING_RESOURCE
    data = {'keep_stacks': 0,
            'new_traffic': 100,
            'image_version': '1.0',
            'senza_yaml': 'SenzaInfo:\n  StackName: abc',
            'parameters': ['abc', 'def'],
            'application_version': '42',
            'stack_version': '10',
            'disable_rollback': True}

    mock_kio.versions_create.return_value = True
    response = app.post('/api/stacks', headers=GOOD_HEADERS,
                        data=json.dumps(data))  # type: flask.Response

    assert response.status_code == 201

    # unusual launch missing TaupageAutoScalingGroup
    mock_kio.reset_mock()
    mock_senza.reset_mock()
    mock_senza.render_definition.return_value = BAD_CF_MISSING_TAUPAGE_AUTOSCALING_GROUP
    data = {'keep_stacks': 0,
            'new_traffic': 100,
            'image_version': '1.0',
            'senza_yaml': 'SenzaInfo:\n  StackName: abc',
            'parameters': ['abc', 'def'],
            'application_version': '42',
            'stack_version': '100',
            'disable_rollback': True}

    mock_kio.versions_create.return_value = True
    response = app.post('/api/stacks', headers=GOOD_HEADERS,
                        data=json.dumps(data))  # type: flask.Response

    assert response.status_code == 400


def test_get_stack(app, oauth_requests, mock_senza):
    parameters = {'version', 'description', 'stack_name', 'status', 'creation_time'}

    request = app.get('/api/stacks/stack-1', headers=GOOD_HEADERS)
    assert request.headers['X-Lizzy-Version'] == CURRENT_VERSION
    response = json.loads(request.data.decode())  # type: dict
    keys = response.keys()
    assert parameters == keys


def test_get_stack_404(app, oauth_requests, mock_senza):
    mock_senza.list = lambda *a, **k: []
    request = app.get('/api/stacks/stack-404', headers=GOOD_HEADERS)
    assert request.status_code == 404
    assert request.headers['X-Lizzy-Version'] == CURRENT_VERSION


def test_delete(app, monkeypatch, mock_senza, oauth_requests):

    request = app.delete('/api/stacks/stack-1', headers=GOOD_HEADERS)
    assert request.status_code == 204
    assert request.headers['X-Lizzy-Version'] == CURRENT_VERSION
    assert len(mock_senza.remove.mock_calls) == 1

    # delete is idempotent
    request = app.delete('/api/stacks/stack-1', headers=GOOD_HEADERS)
    assert request.status_code == 204
    assert request.headers['X-Lizzy-Version'] == CURRENT_VERSION
    assert len(mock_senza.remove.mock_calls) == 2

    request = app.delete('/api/stacks/stack-404', headers=GOOD_HEADERS)
    assert request.status_code == 204
    assert request.headers['X-Lizzy-Version'] == CURRENT_VERSION
    assert len(mock_senza.remove.mock_calls) == 3

    mock_senza.remove.side_effect = ExecutionError('test', 'Error msg')
    request = app.delete('/api/stacks/stack-1', headers=GOOD_HEADERS)
    assert request.status_code == 500
    # TODO test message
    problem = json.loads(request.data.decode())
    assert problem['detail'] == "Error msg"
    assert len(mock_senza.remove.mock_calls) == 4


def test_patch(monkeypatch, app, oauth_requests, mock_senza):
    data = {'new_traffic': 50}

    # Only changes the traffic
    request = app.patch('/api/stacks/stack-1', headers=GOOD_HEADERS,
                        data=json.dumps(data))
    assert request.status_code == 202
    mock_senza.traffic.assert_called_once_with(percentage=50,
                                               stack_name='stack',
                                               stack_version='1')
    assert request.headers['X-Lizzy-Version'] == CURRENT_VERSION

    # Should return 400 when not possible to change the traffic
    # while running the one of the senza commands an error occurs
    mock_senza.traffic.side_effect = SenzaDomainsError('', '')
    request = app.patch('/api/stacks/stack-1', headers=GOOD_HEADERS,
                        data=json.dumps(data))
    assert request.status_code == 400
    mock_senza.traffic.reset()

    # Does not change anything
    request = app.patch('/api/stacks/stack-1', headers=GOOD_HEADERS,
                        data=json.dumps({}))
    assert request.status_code == 202
    assert request.headers['X-Lizzy-Version'] == CURRENT_VERSION

    update_image = {'new_ami_image': 'ami-2323'}

    # Should change the AMI image used by the stack and respawnn the instances
    # using the new AMI image.
    request = app.patch('/api/stacks/stack-1',
                        headers=GOOD_HEADERS,
                        data=json.dumps(update_image))
    assert request.status_code == 202
    assert request.headers['X-Lizzy-Version'] == CURRENT_VERSION
    mock_senza.patch.assert_called_once_with('stack', '1', 'ami-2323')
    mock_senza.respawn_instances.assert_called_once_with('stack', '1')

    # Should return 400 when not possible to change the AMI image
    mock_senza.patch.side_effect = ExecutionError(1, 'fake error')
    request = app.patch('/api/stacks/stack-1', headers=GOOD_HEADERS, data=json.dumps(update_image))
    assert request.status_code == 400


def test_patch404(app, oauth_requests, mock_senza):
    data = {'new_ami_image': 'ami-2323', }
    mock_senza.list = lambda *a, **k: []
    request = app.patch('/api/stacks/stack-404', headers=GOOD_HEADERS,
                        data=json.dumps(data))
    assert request.status_code == 404
    assert request.headers['X-Lizzy-Version'] == CURRENT_VERSION
