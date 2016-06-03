import json
import logging
import os
from typing import List, Optional  # noqa pylint: disable=unused-import

from decorator import decorator

import connexion
import yaml
from flask import Response
from lizzy import config
from lizzy.apps.senza import Senza
from lizzy.exceptions import (ExecutionError, ObjectNotFound,
                              TrafficNotUpdated)
from lizzy.models.stack import Stack
from lizzy.security import bouncer
from lizzy.util import filter_empty_values
from lizzy.version import VERSION

logger = logging.getLogger('lizzy.api')  # pylint: disable=invalid-name


def _make_headers() -> dict:
    return {'X-Lizzy-Version': VERSION}


@decorator
def exception_to_connexion_problem(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except ObjectNotFound as exception:
        problem = connexion.problem(404, 'Not Found',
                                    "Stack not found: {}".format(exception.uid),
                                    headers=_make_headers())
        return problem
    except ExecutionError as error:
        return connexion.problem(500,
                                 title='Execution Error',
                                 detail=error.output,
                                 headers=_make_headers())


@bouncer
@exception_to_connexion_problem
def all_stacks() -> dict:
    """
    GET /stacks/
    """
    stacks = Stack.list()
    stacks.sort(key=lambda stack: stack.creation_time)
    return stacks, 200, _make_headers()


@bouncer
@exception_to_connexion_problem
def create_stack(new_stack: dict) -> dict:
    """
    POST /stacks/

    :param new_stack: New stack
    """

    keep_stacks = new_stack['keep_stacks']  # type: int
    new_traffic = new_stack['new_traffic']  # type: int
    stack_version = new_stack['stack_version']  # type: str
    senza_yaml = new_stack['senza_yaml']  # type: str
    parameters = new_stack.get('parameters', [])
    disable_rollback = new_stack.get('disable_rollback', False)

    try:
        senza_definition = yaml.load(senza_yaml)
    except yaml.YAMLError as exception:
        return connexion.problem(400,
                                 'Invalid senza yaml',
                                 exception.message,
                                 headers=_make_headers())

    try:
        stack_name = senza_definition['SenzaInfo']['StackName']
    except KeyError as exception:
        logger.error("Couldn't get stack name from definition.",
                     extra={'senza_yaml': repr(senza_yaml)})
        missing_property = str(exception)
        problem = connexion.problem(400,
                                    'Invalid senza yaml',
                                    "Missing property in senza yaml: {}".format(
                                        missing_property),
                                    headers=_make_headers())
        return problem

    # Create the Stack
    logger.info("Creating stack %s...", stack_name)

    senza = Senza(config.region)
    tags = {'LizzyKeepStacks': keep_stacks,
            'LizzyTargetTraffic': new_traffic}

    senza.create(senza_yaml, stack_version, parameters, disable_rollback, tags)

    logger.info("Stack created.", extra={'stack_name': stack_name,
                                         'stack_version': stack_version,
                                         'parameters': parameters})
    stack_dict = Stack.get(stack_name, stack_version)
    return stack_dict, 201, _make_headers()


@bouncer
@exception_to_connexion_problem
def get_stack(stack_id: str) -> dict:
    """
    GET /stacks/{id}
    """
    stack_name, stack_version = stack_id.rsplit('-', 1)
    stack_dict = Stack.get(stack_name, stack_version)
    return stack_dict, 200, _make_headers()


@bouncer
@exception_to_connexion_problem
def patch_stack(stack_id: str, stack_patch: dict) -> dict:
    """
    PATCH /stacks/{id}

    Update traffic and Taupage image
    """
    stack_patch = filter_empty_values(stack_patch)

    stack_name, stack_version = stack_id.rsplit('-', 1)
    senza = Senza(config.region)
    log_info = {'stack_id': stack_id,
                'stack_name': stack_name}

    if 'new_ami_image' in stack_patch:
        # Change the AMI image of the Auto Scaling Group (ASG) and respawn the
        # instances to use new image.
        new_ami_image = stack_patch['new_ami_image']
        senza.patch(stack_name, stack_version, new_ami_image)
        senza.respawn_instances(stack_name, stack_version)

    if 'new_traffic' in stack_patch:
        new_traffic = stack_patch['new_traffic']
        domains = senza.domains(stack_name)
        if domains:
            logger.info("Switching app traffic to stack.",
                        extra=log_info)
            senza.traffic(stack_name=stack_name,
                          stack_version=stack_version,
                          percentage=new_traffic)
        else:
            logger.info("App does not have a domain so traffic will not be switched.",
                        extra=log_info)
            raise TrafficNotUpdated("App does not have a domain.")

    # refresh the dict
    stack_dict = Stack.get(stack_name, stack_version)

    return stack_dict, 202, _make_headers()


@bouncer
@exception_to_connexion_problem
def delete_stack(stack_id: str) -> dict:
    """
    DELETE /stacks/{id}

    Delete a stack
    """
    stack_name, stack_version = stack_id.rsplit('-', 1)
    senza = Senza(config.region)

    logger.info("Removing stack %s...", stack_id)

    senza.remove(stack_name, stack_version)
    logger.info("Stack %s removed.", stack_id)

    return '', 204, _make_headers()


def not_found_path_handler(error):
    return connexion.problem(401, 'Unauthorized', '')


def expose_api_schema():
    api_description = json.dumps({
        'schema_type': 'swagger-2.0',
        'schema_url': '/api/swagger.json',
        'ui_url': '/api/ui/'
    })
    return Response(api_description, status=200,
                    headers=_make_headers(),
                    mimetype='application/json')


def get_app_status():
    status = 'OK'
    try:
        Senza(config.region).list()
    except ExecutionError:
        status = 'NOK'

    status_info = {
        'version': os.environ.get("APPLICATION_VERSION", ""),
        'status': status,
        'APIConfig': {
            name: getattr(config, name)
            for name in dir(config) if not name.startswith('__')
        }
    }
    return status_info, 200, _make_headers()


@exception_to_connexion_problem
def health_check():
    Senza(config.region).list()
    return Response(status=200,
                    headers=_make_headers())
