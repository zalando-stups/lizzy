import connexion
import datetime
import flask
import json
import pytest
import requests

import lizzy.api
from lizzy.models.stack import Stack
from lizzy.lizzy import setup_webapp

GOOD_HEADERS = {'Authorization': 'Bearer 100', 'Content-type': 'application/json'}

STACKS = {'stack1': {'stack_id': None,
                     'creation_time': None,
                     'keep_stacks': 1,
                     'traffic': 100,
                     'image_version': 'version',
                     'senza_yaml': 'yaml',
                     'stack_name': 'stackno1',
                     'stack_version': 'v1',
                     'status': 'LIZZY:NEW', }}


class FakeConfig:
    def __init__(self):
        self.deployer_scope = 'myscope'
        self.token_url = 'https://ouath.example/access_token'
        self.token_info_url = 'https://ouath.example/token_info'
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

    @classmethod
    def all(cls):
        return []

    def delete(self):
        pass

    @classmethod
    def get(cls, uid):
        stack = STACKS[uid]
        return cls(**stack)

    def save(self):
        pass


@pytest.fixture
def app(monkeypatch):
    app = setup_webapp(FakeConfig())
    app_client = app.app.test_client()

    monkeypatch.setattr(lizzy.api, 'Stack', FakeStack)

    return app_client


@pytest.fixture
def oauth_requests(monkeypatch: '_pytest.monkeypatch.monkeypatch'):
    def fake_get(url: str, params: dict=None):
        params = params or {}
        if url == "https://ouath.example/token_info":
            token = params['access_token']
            if token == "100":
                return FakeResponse(200, '{"scope": ["myscope"]}')
            if token == "200":
                return FakeResponse(200, '{"scope": ["wrongscope"]}')
            if token == "300":
                return FakeResponse(404, '')
        return url

    monkeypatch.setattr(requests, 'get', fake_get)


def test_security(app, oauth_requests):
    get_swagger = app.get('/api/swagger.json')  # type:flask.Response
    assert get_swagger.status_code == 200

    get_swagger_no_auth = app.get('/api/stacks')  # type:flask.Response
    assert get_swagger_no_auth.status_code == 401

    get_swagger = app.get('/api/stacks', headers=GOOD_HEADERS)
    assert get_swagger.status_code == 200


def test_empty_new_stack(monkeypatch, app, oauth_requests):
    data = {}
    request = app.post('/api/stacks', headers=GOOD_HEADERS, data=json.dumps(data))  # type: flask.Response
    assert request.status_code == 400
    response = json.loads(request.data.decode())
    assert response['title'] == 'Invalid stack'
    assert response['detail'] == "Missing property: 'keep_stacks'"


def test_bad_senza_yaml(app, oauth_requests):
    data = {'keep_stacks': 0,
            'new_traffic': 100,
            'image_version': '1.0',
            'senza_yaml': 'key: value'}

    request = app.post('/api/stacks', headers=GOOD_HEADERS, data=json.dumps(data))  # type: flask.Response
    assert request.status_code == 400
    response = json.loads(request.data.decode())
    assert response['title'] == 'Invalid senza yaml'
    assert response['detail'] == "Missing property in senza yaml: 'SenzaInfo'"

    data['senza_yaml'] = '[]'
    request = app.post('/api/stacks', headers=GOOD_HEADERS, data=json.dumps(data))  # type: flask.Response
    assert request.status_code == 400
    response = json.loads(request.data.decode())
    assert response['title'] == 'Invalid senza yaml'
    assert response['detail'] == "Senza yaml is not a dict."


def test_new_stack(app, oauth_requests):
    data = {'keep_stacks': 0,
            'new_traffic': 100,
            'image_version': '1.0',
            'senza_yaml': 'SenzaInfo:\n  StackName: abc'}

    request = app.post('/api/stacks', headers=GOOD_HEADERS, data=json.dumps(data))  # type: flask.Response
    assert request.status_code == 201


def test_get_stack(app, oauth_requests):
    parameters = ['stack_version', 'stack_name', 'senza_yaml', 'creation_time', 'image_version', 'status', 'stack_id']

    request = app.get('/api/stacks/stack1', headers=GOOD_HEADERS)
    assert request.status_code == 200
    response = json.loads(request.data.decode())  # type: dict
    keys = response.keys()
    for parameter in parameters:
        assert parameter in keys


def test_get_stack_404(app, oauth_requests):
    request = app.get('/api/stacks/stack404', headers=GOOD_HEADERS)
    assert request.status_code == 404
