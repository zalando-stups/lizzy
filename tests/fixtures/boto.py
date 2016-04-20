from unittest.mock import MagicMock

import pytest


@pytest.fixture
def cf(monkeypatch):
    cf = MagicMock()
    stack = {'Tags': [{'Key': 'abc',
                       'Value': '42'}]}
    stacks = {'Stacks': [stack]}
    cf.describe_stacks.return_value = stacks
    monkeypatch.setattr('boto3.client', lambda *args: cf)
    return cf
