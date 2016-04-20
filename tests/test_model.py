from unittest.mock import MagicMock, call, ANY
import botocore.exceptions

from lizzy.models.stack import Stack
from fixtures.boto import cf

YAML1 = """
SenzaInfo:
  Parameters:
  - ImageVersion: {Description: Docker image version of lizzy.}
  - Test: {Description: Docker image version of lizzy.}
  - DefaultTest: {Description: Docker image version of lizzy., Default: defaultTestValue}
  StackName: lizzy
Test: lizzy:{{Arguments.ImageVersion}}
Test2: lizzy:{{Arguments.Test}}
Test3: lizzy:{{Arguments.DefaultTest}}
"""


def test_cf_tags(monkeypatch, cf):
    stack = Stack(stack_id='lizzy-42', creation_time='2015-09-16T09:48',
                  keep_stacks=2, traffic=7, image_version='1.0',
                  senza_yaml=YAML1, stack_name='lizzy', stack_version='42',
                  parameters=['testValue'],
                  status='LIZZY:TEST')

    assert stack.cf_tags == {'abc': '42'}


def test_cf_tags_error(monkeypatch, cf):
    cf.describe_stacks.side_effect = botocore.exceptions.ClientError({'Error': {}}, 'describe')
    stack = Stack(stack_id='lizzy-42', creation_time='2015-09-16T09:48',
                  keep_stacks=2, traffic=7, image_version='1.0',
                  senza_yaml=YAML1, stack_name='lizzy', stack_version='42',
                  parameters=['testValue'],
                  status='LIZZY:TEST')

    assert stack.cf_tags == {}
