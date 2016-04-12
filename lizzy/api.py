import logging

import connexion
import yaml
from decorator import decorator
from lizzy import config
from lizzy.apps.kio import Kio
from lizzy.apps.senza import Senza
from lizzy.deployer import InstantDeployer
from lizzy.exceptions import (AMIImageNotUpdated, ObjectNotFound,
                              SenzaRenderError, StackDeleteException,
                              TrafficNotUpdated)
from lizzy.models.stack import Stack
from lizzy.security import bouncer
from lizzy.util import filter_empty_values
from lizzy.version import VERSION
from typing import Optional  # noqa

logger = logging.getLogger('lizzy.api')


def _make_headers() -> dict:
    return {'X-Lizzy-Version': VERSION}


def _get_stack_dict(stack: Stack) -> dict:
    """
    .. seealso:: lizzy/swagger/lizzy.yaml#/definitions/stack
    """
    stack_dict = {'stack_id': stack.stack_id,
                  'creation_time': '{:%FT%T%z}'.format(stack.creation_time),
                  'image_version': stack.image_version,
                  'parameters': stack.parameters,
                  'application_version': stack.application_version,
                  'senza_yaml': stack.senza_yaml,
                  'stack_name': stack.stack_name,
                  'stack_version': stack.stack_version,
                  'status': stack.status}
    return stack_dict


@decorator
def exception_to_connexion_problem(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except ObjectNotFound as e:
        problem = connexion.problem(404, 'Not Found',
                                    "Stack not found: {}".format(e.uid),
                                    headers=_make_headers())
        return problem


@bouncer
def all_stacks() -> dict:
    """
    GET /stacks/
    """
    stacks = [_get_stack_dict(stack) for stack in Stack.all()]
    stacks.sort(key=lambda stack: stack['creation_time'])
    return stacks, 200, _make_headers()


@bouncer
def create_stack(new_stack: dict) -> dict:
    """
    POST /stacks/

    :param new_stack: New stack
    """

    keep_stacks = new_stack['keep_stacks']  # type: int
    new_traffic = new_stack['new_traffic']  # type: int
    image_version = new_stack['image_version']  # type: str
    application_version = new_stack.get('application_version')  # type: Optional[str]
    stack_version = new_stack.get('stack_version')  # type: Optional[str]
    senza_yaml = new_stack['senza_yaml']  # type: str
    parameters = new_stack.get('parameters', [])
    disable_rollback = new_stack.get('disable_rollback', False)
    stack_name = None
    artifact_name = None
    cf_raw_definition = None
    senza = Senza(config.region)

    stack = Stack(keep_stacks=keep_stacks,
                  traffic=new_traffic,
                  image_version=image_version,
                  senza_yaml=senza_yaml,
                  stack_name=stack_name,
                  stack_version=stack_version,
                  application_version=application_version,
                  parameters=parameters)

    try:
        cf_raw_definition = senza.render_definition(senza_yaml,
                                                    stack.stack_version,
                                                    stack.image_version,
                                                    parameters)
    except SenzaRenderError as exception:
        return connexion.problem(400,
                                 'Invalid senza yaml',
                                 exception.message,
                                 headers=_make_headers())

    try:
        stack_name = cf_raw_definition['Mappings']['Senza']['Info']['StackName']

        for resource, definition in cf_raw_definition['Resources'].items():
            if definition['Type'] == 'AWS::AutoScaling::LaunchConfiguration':
                taupage_yaml = definition['Properties']['UserData']['Fn::Base64']
                taupage_config = yaml.safe_load(taupage_yaml)
                artifact_name = taupage_config['source']

        if artifact_name is None:
            missing_component_error = "Missing component type Senza::TaupageAutoScalingGroup"
            problem = connexion.problem(400,
                                        'Invalid senza yaml',
                                        missing_component_error,
                                        headers=_make_headers())

            logger.error(missing_component_error, extra={
                'cf_definition': repr(cf_raw_definition)})
            return problem

    except KeyError as exception:
        logger.error("Couldn't get stack name from definition.",
                     extra={'cf_definition': repr(cf_raw_definition)})
        missing_property = str(exception)
        problem = connexion.problem(400,
                                    'Invalid senza yaml',
                                    "Missing property in senza yaml: {}".format(missing_property),
                                    headers=_make_headers())
        return problem

    # Create the Stack
    logger.info("Creating stack %s...", stack_name)
    stack.stack_name = stack_name
    stack.stack_id = stack.generate_id()

    if stack.application_version:
        kio_extra = {'stack_name': stack_name, 'version': application_version}
        logger.info("Registering version on kio...", extra=kio_extra)
        kio = Kio()
        if kio.versions_create(application_id=stack.stack_name,
                               version=stack.application_version,
                               artifact=artifact_name):
            logger.info("Version registered in Kio.", extra=kio_extra)
        else:
            logger.error("Error registering version in Kio.", extra=kio_extra)

    senza = Senza(config.region)
    stack_extra = {'stack_name': stack_name,
                   'stack_version': stack.stack_version,
                   'image_version': stack.image_version,
                   'parameters': stack.parameters}
    if senza.create(stack.senza_yaml, stack.stack_version, stack.image_version,
                    stack.parameters, disable_rollback):
        logger.info("Stack created.", extra=stack_extra)
        # Mark the stack as CREATE_IN_PROGRESS. Even if this isn't true anymore
        # this will be handled in the job anyway
        stack.status = 'CF:CREATE_IN_PROGRESS'
        stack.save()
        return _get_stack_dict(stack), 201, _make_headers()
    else:
        logger.error("Error creating stack.", extra=stack_extra)
        return connexion.problem(400, 'Deployment Failed',
                                 "Senza create command failed.",
                                 headers=_make_headers())


@bouncer
@exception_to_connexion_problem
def get_stack(stack_id: str) -> dict:
    """
    GET /stacks/{id}
    """
    stack = Stack.get(stack_id)
    return _get_stack_dict(stack), 200, _make_headers()


@bouncer
@exception_to_connexion_problem
def patch_stack(stack_id: str, stack_patch: dict) -> dict:
    """
    PATCH /stacks/{id}

    Update traffic and Taupage image
    """
    stack_patch = filter_empty_values(stack_patch)

    stack = Stack.get(stack_id)
    deployer = InstantDeployer(stack)

    if 'new_ami_image' in stack_patch:
        new_ami_image = stack_patch['new_ami_image']
        try:
            deployer.update_ami_image(new_ami_image)
            stack.ami_image = new_ami_image
        except AMIImageNotUpdated as e:
            return connexion.problem(400, 'Image update failed', e.message,
                                     headers=_make_headers())

    if 'new_traffic' in stack_patch:
        new_traffic = stack_patch['new_traffic']
        try:
            deployer.change_traffic(new_traffic)
        except TrafficNotUpdated as e:
            return connexion.problem(400, 'Traffic update failed', e.message,
                                     headers=_make_headers())
        stack.traffic = new_traffic

    stack.save()

    return _get_stack_dict(stack), 202, _make_headers()


@bouncer
def delete_stack(stack_id: str) -> dict:
    """
    DELETE /stacks/{id}

    Delete a stack
    """
    try:
        stack = Stack.get(stack_id)
    except ObjectNotFound:
        # delete is idempotent, if the stack is not there it just
        # doesn't do anything.
        pass
    else:
        deployer = InstantDeployer(stack)
        try:
            deployer.delete_stack()
        except StackDeleteException as e:
            return connexion.problem(500, 'Stack deletion failed', e.message,
                                     headers=_make_headers())

    return '', 204, _make_headers()
