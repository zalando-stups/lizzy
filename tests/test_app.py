import json
import os
from unittest.mock import MagicMock
from urllib.parse import quote

import lizzy.api
import pytest
import requests
from fixtures.cloud_formation import (BAD_CF_DEFINITION, GOOD_CF_DEFINITION,
                                      GOOD_CF_DEFINITION_WITH_UNUSUAL_AUTOSCALING_RESOURCE)
from lizzy.configuration import config
from lizzy.exceptions import (ExecutionError, SenzaDomainsError,
                              SenzaRenderError)
from lizzy.models.stack import Stack
from lizzy.service import setup_webapp
from lizzy.version import VERSION
from senza import __version__ as SENZA_VERSION

CURRENT_VERSION = VERSION

GOOD_HEADERS = {'Authorization': 'Bearer 100',
                'Content-type': 'application/json'}

STACKS = {'stack-1': {'stack_id': None,
                      'creation_time': None,
                      'keep_stacks': 1,
                      'traffic': 100,
                      'image_version': 'version',
                      'ami_image': 'latest',
                      'senza_yaml': 'yaml',
                      'stack_name': 'stackno1',
                      'stack_version': 'v1',
                      'status': 'LIZZY:NEW'}}


class FakeConfig:
    def __init__(self):
        self.deployer_scope = 'myscope'
        self.token_url = 'https://ouath.example/access_token'
        self.port = 8080
        self.sentry_dsn = None


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
                    return FakeResponse(200,
                                        '{"scope": ["myscope"], "uid": "test_user"}')
                if token == "200":
                    return FakeResponse(200,
                                        '{"scope": ["wrongscope"], , "uid": "test_user"}')
                if token == "300":
                    return FakeResponse(404, '')
            return url

    monkeypatch.setattr('connexion.decorators.security.session', Session())


def test_security(app, mock_senza):
    get_swagger = app.get('/api/swagger.json')  # type:flask.Response
    assert get_swagger.status_code == 200

    get_stacks_no_auth = app.get('/api/stacks')  # type:flask.Response
    assert get_stacks_no_auth.status_code == 401

    get_stacks = app.get('/api/stacks', headers=GOOD_HEADERS)
    assert get_stacks.status_code == 200
    assert get_stacks.headers['X-Lizzy-Version'] == CURRENT_VERSION
    assert get_stacks.headers['X-Senza-Version'] == SENZA_VERSION

    inexistent_url = app.get('/api/does-not-exist', headers=GOOD_HEADERS)
    assert inexistent_url.status_code == 404

    invalid_access = app.get('/api/does-not-exist')
    assert invalid_access.status_code == 401

    invalid_access = app.get(
        '/random-access-that-does-not-exist-outside-of-api')
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

    monkeypatch.setattr(lizzy.security, 'Configuration',
                        AllowedOtherUsersConfig)
    monkeypatch.setattr(lizzy.api, 'Stack', FakeStack)

    stacks_response = app_client.get('/api/stacks', headers=GOOD_HEADERS)
    assert stacks_response.status_code == 200


def test_security_now_allowed_user_pattern(monkeypatch, mock_senza):
    os.environ['TOKENINFO_URL'] = 'https://ouath.example/token_info'

    class AllowedOtherUsersConfig(FakeConfig):
        def __init__(self):
            super().__init__()
            self.allowed_users = None
            self.allowed_user_pattern = '^somethingelse_.*'

    app = setup_webapp(AllowedOtherUsersConfig())
    app_client = app.app.test_client()

    monkeypatch.setattr(lizzy.security, 'Configuration',
                        AllowedOtherUsersConfig)
    monkeypatch.setattr(lizzy.api, 'Stack', FakeStack)

    stacks_response = app_client.get('/api/stacks', headers=GOOD_HEADERS)
    assert stacks_response.status_code == 403


def test_empty_new_stack(monkeypatch, app):
    data = {}
    request = app.post('/api/stacks', headers=GOOD_HEADERS,
                       data=json.dumps(data))  # type: flask.Response
    assert request.status_code == 400
    response = json.loads(request.data.decode())
    assert response['title'] == 'Bad Request'


def test_bad_senza_yaml(app, monkeypatch, mock_senza):
    data = {'keep_stacks': 0,
            'stack_version': 1,
            'new_traffic': 100,
            'image_version': '1.0',
            'stack_version': '40',
            'senza_yaml': 'key: value'}

    mock_senza = MagicMock()
    mock_senza.return_value = mock_senza
    monkeypatch.setattr('lizzy.api.Senza', mock_senza)
    mock_senza.render_definition.side_effect = SenzaRenderError("Some error",
                                                                "output error")

    request = app.post('/api/stacks', headers=GOOD_HEADERS,
                       data=json.dumps(data))  # type: flask.Response
    assert request.status_code == 400
    response = json.loads(request.data.decode())
    assert response['title'] == 'Invalid senza yaml'
    assert request.headers['X-Lizzy-Version'] == CURRENT_VERSION
    assert request.headers['X-Senza-Version'] == SENZA_VERSION

    mock_senza = MagicMock()
    mock_senza.return_value = mock_senza
    monkeypatch.setattr('lizzy.api.Senza', mock_senza)
    mock_senza.render_definition.return_value = BAD_CF_DEFINITION


@pytest.mark.parametrize(
    "definition, version, parameters, region, disable_rollback, dry_run, force, tags, keep_stacks, new_traffic",
    [
        (GOOD_CF_DEFINITION, "new_version", ['10'], None, True, False, False, [], 0, 100),
        (GOOD_CF_DEFINITION, "1", ["1.0"], "eu-central-1", False, True, False, [], 0, 100),
        (GOOD_CF_DEFINITION, "42", ['abc', 'def'], "eu-central-1", False, False, True, [], 42, 42),
        (GOOD_CF_DEFINITION, "7", ['abc', 'def'], "eu-central-1", True, False, True, [], 50, 40),
        (GOOD_CF_DEFINITION, "42", ['MintBucket=bk', 'ImageVersion=28'], None, True, False, True, [], 100, 0),
        (GOOD_CF_DEFINITION,
            "42", ['MintBucket=bk', 'ImageVersion=28'], None, True, False, True,
            ['tag1=value1', 'tag2=value2'], 100, 0),
        (GOOD_CF_DEFINITION_WITH_UNUSUAL_AUTOSCALING_RESOURCE,
            "new_version", ['10'], None, True, False, False, [], 0, 100),
    ])
def test_new_stack(app, mock_senza,
                   version, parameters, region, disable_rollback, dry_run,
                   force, tags, keep_stacks, new_traffic, definition):
    data = {'keep_stacks': keep_stacks,
            'new_traffic': new_traffic,
            'parameters': parameters,
            'stack_version': version,
            'senza_yaml': 'SenzaInfo:\n  StackName: abc',
            'tags': tags}

    if region:
        data["region"] = region
    else:
        region = 'eu-west-1'

    if disable_rollback is not None:
        data["disable_rollback"] = disable_rollback

    if dry_run is not None:
        data["dry_run"] = dry_run
    mock_senza.reset()
    mock_senza.render_definition.return_value = definition

    request = app.post('/api/stacks',
                       headers=GOOD_HEADERS,
                       data=json.dumps(data))  # type: flask.Response
    mock_senza.assert_called_with(region)

    expected_tags = ['LizzyKeepStacks={}'.format(keep_stacks),
                     'LizzyTargetTraffic={}'.format(new_traffic)] + tags
    mock_senza.create.assert_called_with('SenzaInfo:\n  StackName: abc',
                                         version, parameters,
                                         disable_rollback, dry_run,
                                         expected_tags)
    assert request.status_code == 201
    assert request.headers['X-Lizzy-Version'] == CURRENT_VERSION
    assert request.headers['X-Senza-Version'] == SENZA_VERSION
    response = json.loads(request.get_data().decode())
    assert len(response) == 5
    assert response['stack_name'] == 'abc'
    assert response['version'] == version
    if dry_run:
        assert response['creation_time'] == ''
        assert response['status'] == 'DRY-RUN'
        assert response['description'] == ''
    else:
        assert response['creation_time'] == '2016-04-14T11:59:27+00:00'
        assert response['status'] == 'CREATE_COMPLETE'
        assert response['description'] == 'Lizzy Bus (ImageVersion: 257)'


def test_new_stack_execution_error(monkeypatch, app, mock_senza):

    mock_senza.render_definition.return_value = GOOD_CF_DEFINITION

    mock_senza.create.side_effect = ExecutionError(2, "error")
    data = {'keep_stacks': 0,
            'new_traffic': 100,
            'stack_version': '43',
            'senza_yaml': 'SenzaInfo:\n  StackName: abc',
            'parameters': ['MintBucket=bk-bucket', 'ImageVersion=28'],
            'dry_run': True}

    request = app.post('/api/stacks',
                       headers=GOOD_HEADERS,
                       data=json.dumps(data))  # type: flask.Response
    assert request.status_code == 500
    error_data = json.loads(request.data.decode())
    assert error_data['detail'] == 'error'


def test_get_stack(app, mock_senza):
    parameters = {'version', 'description', 'stack_name', 'status',
                  'creation_time'}

    response = app.get('/api/stacks/stack-1', headers=GOOD_HEADERS)
    assert response.headers['X-Lizzy-Version'] == CURRENT_VERSION
    assert response.headers['X-Senza-Version'] == SENZA_VERSION    
    payload = json.loads(response.data.decode())  # type: dict
    assert parameters == payload.keys()

    mock_senza.reset_mock()
    response = app.get('/api/stacks/stack-1?region=br-south-1', headers=GOOD_HEADERS)
    assert response.status_code == 200
    mock_senza.assert_called_with('br-south-1')
    mock_senza.list.assert_called_with('stack', '1')

    mock_senza.reset_mock()
    response = app.get('/api/stacks/stack-1?region=crazy-1', headers=GOOD_HEADERS)
    assert response.status_code == 400


def test_list_stacks(app, mock_senza):
    response = app.get('/api/stacks', headers=GOOD_HEADERS)
    payload = json.loads(response.data.decode())  # type: dict
    assert len(payload) > 0
    assert response.status_code == 200
    mock_senza.assert_called_with(config.region)
    mock_senza.list.assert_called_with()

    response = app.get('/api/stacks?references={}'.format(quote('stack,v2')), headers=GOOD_HEADERS)
    payload = json.loads(response.data.decode())  # type: dict
    assert len(payload) > 0
    assert response.status_code == 200
    mock_senza.assert_called_with(config.region)
    mock_senza.list.assert_called_with('stack', 'v2')

    # request invalid region format
    response = app.get('/api/stacks?region=abc', headers=GOOD_HEADERS)
    assert response.status_code == 400
    assert "'abc' does not match" in response.data.decode()

    # request with valid region format
    response = app.get('/api/stacks?region=fo-barbazz-7', headers=GOOD_HEADERS)
    assert response.status_code == 200
    mock_senza.assert_called_with('fo-barbazz-7')
    mock_senza.list.assert_called_with()


def test_get_stack_404(app, mock_senza):
    mock_senza.list = lambda *a, **k: []
    request = app.get('/api/stacks/stack-404', headers=GOOD_HEADERS)
    assert request.status_code == 404
    assert request.headers['X-Lizzy-Version'] == CURRENT_VERSION
    assert request.headers['X-Senza-Version'] == SENZA_VERSION


@pytest.mark.parametrize(
    "stack_id, region, dry_run, force",
    [
        ('stack-1', 'eu-west-1', False, True),
        ('stack-1', 'eu-central-1', True, True),
        ('stack-1', 'eu-west-1', False, False),
        ('stack-1', 'eu-central-1', True, False),
        ('stack-404', 'eu-west-1', False, True),  # Non existing stack
        ('stack-404', 'eu-central-1', True, True),
        ('stack-404', 'eu-west-1', False, False),
        ('stack-404', 'eu-central-1', True, False),
        ('stackwithoutversion', 'eu-west-1', False, True),
        ('stackwithoutversion', 'eu-central-1', True, True),
        ('stackwithoutversion', 'eu-west-1', False, False),
        ('stackwithoutversion', 'eu-central-1', True, False),

    ])
def test_delete(app, mock_senza, stack_id, region, dry_run, force):
    url = '/api/stacks/' + stack_id
    data = {'region': region, 'dry_run': dry_run, 'force': force}
    request = app.delete(url, data=json.dumps(data), headers=GOOD_HEADERS)
    assert request.status_code == 204
    assert request.headers['X-Lizzy-Version'] == CURRENT_VERSION
    assert request.headers['X-Senza-Version'] == SENZA_VERSION
    mock_senza.assert_called_once_with(region)
    mock_senza.remove.assert_called_once_with(stack_id,
                                              dry_run=dry_run, force=force)

    # delete is idempotent
    request = app.delete(url, data=json.dumps(data), headers=GOOD_HEADERS)
    assert request.status_code == 204
    assert request.headers['X-Lizzy-Version'] == CURRENT_VERSION
    assert request.headers['X-Senza-Version'] == SENZA_VERSION


@pytest.mark.parametrize(
    "dry_run, force",
    [
        (False, True),
        (True, True),
        (False, False),
        (True, False),
    ])
def test_delete_error(app, mock_senza, dry_run, force):
    data = {'dry_run': dry_run, 'force': force}
    mock_senza.remove.side_effect = ExecutionError('test', 'Error msg')
    request = app.delete('/api/stacks/stack-1', data=json.dumps(data), headers=GOOD_HEADERS)
    assert request.status_code == 500
    # TODO test message
    problem = json.loads(request.data.decode())
    assert problem['detail'] == "Error msg"
    mock_senza.remove.assert_called_once_with('stack-1',
                                              dry_run=dry_run, force=force)


def test_patch(monkeypatch, app, mock_senza):
    data = {'new_traffic': 50}

    # Only changes the traffic
    request = app.patch('/api/stacks/stack-1', headers=GOOD_HEADERS,
                        data=json.dumps(data))
    assert request.status_code == 202
    mock_senza.traffic.assert_called_once_with(percentage=50,
                                               stack_name='stack',
                                               stack_version='1')
    assert request.headers['X-Lizzy-Version'] == CURRENT_VERSION
    assert request.headers['X-Senza-Version'] == SENZA_VERSION

    # Should return 500 when not possible to change the traffic
    # while running the one of the senza commands an error occurs
    # the error is exposed to the client
    mock_senza.traffic.side_effect = SenzaDomainsError('', '')
    request = app.patch('/api/stacks/stack-1', headers=GOOD_HEADERS,
                        data=json.dumps(data))
    assert request.status_code == 500
    mock_senza.traffic.reset()

    # Does not change anything
    request = app.patch('/api/stacks/stack-1', headers=GOOD_HEADERS,
                        data=json.dumps({}))
    assert request.status_code == 202
    assert request.headers['X-Lizzy-Version'] == CURRENT_VERSION
    assert request.headers['X-Senza-Version'] == SENZA_VERSION

    # Run in a different region
    mock_senza.traffic.reset()
    data_for_another_region = {'new_traffic': 50, 'region': 'ee-foobar-8'}
    request = app.patch('/api/stacks/stack-1', headers=GOOD_HEADERS,
                        data=json.dumps(data_for_another_region))
    mock_senza.assert_called_with('ee-foobar-8')

    update_image = {'new_ami_image': 'ami-2323'}

    # Should change the AMI image used by the stack and respawn the instances
    # using the new AMI image.
    request = app.patch('/api/stacks/stack-1',
                        headers=GOOD_HEADERS,
                        data=json.dumps(update_image))
    assert request.status_code == 202
    assert request.headers['X-Lizzy-Version'] == CURRENT_VERSION
    assert request.headers['X-Senza-Version'] == SENZA_VERSION
    mock_senza.patch.assert_called_once_with('stack', '1', 'ami-2323')
    mock_senza.respawn_instances.assert_called_once_with('stack', '1')

    # Should return 500 when not possible to change the AMI image
    mock_senza.patch.side_effect = ExecutionError(1, 'fake error')
    request = app.patch('/api/stacks/stack-1', headers=GOOD_HEADERS,
                        data=json.dumps(update_image))
    assert request.status_code == 500


def test_get_traffic(monkeypatch, app, mock_senza):
    traffic_output_from_senza = [
        {
            "identifier": "foo-v2",
            "stack_name": "foo",
            "version": "v2",
            "weight%": 10.0
        },
        {
            "identifier": "foo-v1",
            "stack_name": "foo",
            "version": "v1",
            "weight%": 90.0
        }
    ]

    # case when everything works fine
    mock_senza.traffic.return_value = traffic_output_from_senza
    response = app.get('/api/stacks/foo-v1/traffic', headers=GOOD_HEADERS)
    assert response.status_code == 200
    payload = json.loads(response.data.decode())
    assert payload['weight'] == 90.0

    # case when cannot find the version
    mock_senza.traffic.return_value = []
    response = app.get('/api/stacks/foo-v1/traffic', headers=GOOD_HEADERS)
    assert response.status_code == 404

    # request invalid region format
    response = app.get('/api/stacks/foo-v1/traffic?region=abc', headers=GOOD_HEADERS)
    assert response.status_code == 400
    assert "'abc' does not match" in response.data.decode()

    # request with valid region format
    mock_senza.traffic.return_value = traffic_output_from_senza
    response = app.get('/api/stacks/foo-v1/traffic?region=fo-barbazz-7', headers=GOOD_HEADERS)
    assert response.status_code == 200
    mock_senza.assert_called_with('fo-barbazz-7')


def test_patch404(app, mock_senza):
    data = {'new_ami_image': 'ami-2323'}
    mock_senza.list = lambda *a, **k: []
    response = app.patch('/api/stacks/stack-404', headers=GOOD_HEADERS,
                         data=json.dumps(data))
    assert response.status_code == 404
    assert response.headers['X-Lizzy-Version'] == CURRENT_VERSION
    assert response.headers['X-Senza-Version'] == SENZA_VERSION


def test_api_discovery_endpoint(app):
    response = app.get('/.well-known/schema-discovery')
    assert response.status_code == 200

    payload = json.loads(response.data.decode())
    assert payload['schema_type'] == 'swagger-2.0'
    assert payload['schema_url'] == '/api/swagger.json'
    assert payload['ui_url'] == '/api/ui/'


def test_application_status_endpoint(app, mock_senza):
    os.environ['DEPLOYER_SCOPE'] = 'can_deploy'
    os.environ['TOKEN_URL'] = 'https://tokenservice.example.com'
    response = app.get('/api/status', headers=GOOD_HEADERS)
    assert response.status_code == 200

    payload = json.loads(response.data.decode())
    assert payload['status'] == 'OK'


def test_application_status_endpoint_when_nok(app, mock_senza):
    os.environ['DEPLOYER_SCOPE'] = 'can_deploy'
    os.environ['TOKEN_URL'] = 'https://tokenservice.example.com'
    mock_senza.list = MagicMock(side_effect=ExecutionError('test', 'Error'))

    response = app.get('/api/status', headers=GOOD_HEADERS)
    assert response.status_code == 200

    payload = json.loads(response.data.decode())
    assert payload['status'] == 'NOK'


def test_application_status_endpoint_when_not_authenticated(app, mock_senza):
    response = app.get('/api/status')
    assert response.status_code == 401


def test_health_check_endpoint(app, mock_senza):
    mock_senza.list = MagicMock()

    response = app.get('/health')
    assert response.status_code == 200

    mock_senza.list.assert_called_with()


def test_health_check_failing(app, mock_senza):
    mock_senza.list = MagicMock(side_effect=ExecutionError(2, "error"))

    response = app.get('/health')
    assert response.status_code == 500

def test_request_count(app, mock_aws):
    mock_aws.get_load_balancer_info.return_value = 'lb-id', 'lb-type'
    mock_aws.get_request_count.return_value = 3185

    response = app.get('/api/stacks/stack_name-stack_version/request_count', headers=GOOD_HEADERS)
    assert response.status_code == 200
    mock_aws.get_load_balancer_info.assert_called_with('stack_name-stack_version')
    mock_aws.get_request_count.assert_called_with('lb-id', 'lb-type', 5)

    assert json.loads(response.data.decode()) == {'request_count': 3185}

def test_request_count_set_minutes(app, mock_aws):
    mock_aws.get_load_balancer_info.return_value = 'lb-id', 'lb-type'
    mock_aws.get_request_count.return_value = 3185

    response = app.get('/api/stacks/stack_name-stack_version/request_count?minutes=15', headers=GOOD_HEADERS)
    assert response.status_code == 200
    mock_aws.get_load_balancer_info.assert_called_with('stack_name-stack_version')
    mock_aws.get_request_count.assert_called_with('lb-id', 'lb-type', 15)

    assert json.loads(response.data.decode()) == {'request_count': 3185}

def test_request_count_set_minutes_invalid(app, mock_aws):
    mock_aws.get_request_count.return_value = 3185

    response = app.get('/api/stacks/stack_name-stack_version/request_count?minutes=0', headers=GOOD_HEADERS)
    assert response.status_code == 400
