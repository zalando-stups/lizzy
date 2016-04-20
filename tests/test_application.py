import pytest
from unittest.mock import MagicMock
import json

from lizzy.apps.common import Application
from lizzy.exceptions import ExecutionError


@pytest.fixture
def popen(monkeypatch):
    mock_popen = MagicMock()
    mock_popen.return_value = mock_popen
    mock_popen.returncode = 0
    monkeypatch.setattr('lizzy.apps.common.Popen', mock_popen)
    return mock_popen


def test_json_output(monkeypatch, popen):
    expected = {"foo": "bar"}
    popen.communicate.return_value = json.dumps(expected).encode(), b'stderr'

    app = Application("foo")
    output = app._execute("bar", "a", "b", "c", expect_json=True, accept_empty=True)
    assert output == expected

    output = app._execute("bar", "a", "b", "c", expect_json=False, accept_empty=True)
    assert output == json.dumps(expected)

    output = app._execute("bar", "a", "b", "c", expect_json=True, accept_empty=False)
    assert output == expected

    output = app._execute("bar", "a", "b", "c", expect_json=False, accept_empty=False)
    assert output == json.dumps(expected)


def test_empty_output(monkeypatch, popen):
    expected = ""
    popen.communicate.return_value = expected.encode(), b'stderr'

    app = Application("foo")

    output = app._execute("bar", "a", "b", "c", expect_json=False, accept_empty=True)
    assert output == expected

    output = app._execute("bar", "a", "b", "c", expect_json=True, accept_empty=True)
    assert output == expected

    with pytest.raises(ExecutionError):
        app._execute("bar", "a", "b", "c", expect_json=True, accept_empty=False)

    with pytest.raises(ExecutionError):
        app._execute("bar", "a", "b", "c", expect_json=False, accept_empty=False)


def test_invalid_json_output(monkeypatch, popen):
    expected = "[[}"
    popen.communicate.return_value = expected.encode(), b'stderr'

    app = Application("foo")
    output = app._execute("bar", "a", "b", "c", expect_json=False, accept_empty=True)
    assert output == expected

    output = app._execute("bar", "a", "b", "c", expect_json=False, accept_empty=False)
    assert output == expected

    with pytest.raises(ExecutionError):
        app._execute("bar", "a", "b", "c", expect_json=True, accept_empty=False)

    with pytest.raises(ExecutionError):
        app._execute("bar", "a", "b", "c", expect_json=True, accept_empty=True)
