from unittest.mock import MagicMock
import pytest

from lizzy.job.deployer import Deployer
from lizzy.models.stack import Stack

LIZZY_STACKS = {'stack-1': {'stack_id': 'stack-1',
                            'creation_time': '2015-09-15',
                            'keep_stacks': 1,
                            'traffic': 100,
                            'image_version': 'version',
                            'senza_yaml': 'yaml',
                            'stack_name': 'stackno1',
                            'stack_version': 'v1',
                            'status': 'LIZZY:NEW',
                            'parameters': ['parameter1', 'parameter2']},
                'lizzyremoved-1': {'stack_id': 'lizzyremoved-1',
                                   'creation_time': '2015-09-15',
                                   'keep_stacks': 1,
                                   'traffic': 100,
                                   'image_version': 'version',
                                   'senza_yaml': 'yaml',
                                   'stack_name': 'stackno1',
                                   'stack_version': 'v1',
                                   'status': 'LIZZY:REMOVED',
                                   'parameters': ['parameter1', 'parameter2']}}

CF_STACKS = {'lizzy': {'42': {'status': 'TEST:STATE'}}}


def test_log_info():
    stack = Stack(stack_id='lizzy-42', creation_time='2015-09-16T09:48', keep_stacks=2, traffic=7, image_version='1.0',
                  senza_yaml='senza:yaml', stack_name='lizzy', stack_version='42', parameters=[], status='LIZZY:TEST')
    deployer = Deployer('region', LIZZY_STACKS, CF_STACKS, stack)
    assert deployer.log_info == {'cf_status': 'TEST:STATE',
                                 'lizzy.stack.id': 'lizzy-42',
                                 'lizzy.stack.name': 'lizzy',
                                 'lizzy.stack.traffic': 7}
