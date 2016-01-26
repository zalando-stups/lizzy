from lizzy.models.stack import Stack

YAML1 = """
SenzaInfo:
  Parameters:
  - ImageVersion: {Description: Docker image version of lizzy.}
  StackName: lizzy
Test: lizzy:{{Arguments.ImageVersion}}
"""


def test_definition_generator():
    stack = Stack(stack_id='lizzy-42', creation_time='2015-09-16T09:48', keep_stacks=2, traffic=7, image_version='1.0',
                  senza_yaml=YAML1, stack_name='lizzy', stack_version='42', parameters=['version42'],
                  status='LIZZY:TEST')

    definition1 = stack.generate_definition()

    assert definition1['Test'] == 'lizzy:version42'
