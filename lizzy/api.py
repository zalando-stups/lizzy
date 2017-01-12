import json
import logging
import os
from typing import (Dict, List, Optional,  # noqa pylint: disable=unused-import
                    Tuple)

import connexion
import yaml
from decorator import decorator
from flask import Response
from lizzy import config, metrics, sentry_client
from lizzy.apps.senza import Senza
from lizzy.exceptions import ExecutionError, ObjectNotFound, TrafficNotUpdated
from lizzy.metrics import MeasureRunningTime
from lizzy.models.stack import Stack
from lizzy.security import bouncer
from lizzy.util import filter_empty_values
from lizzy.version import VERSION

logger = logging.getLogger('lizzy.api')  # pylint: disable=invalid-name


def _make_headers(**kwargs: Dict[str, str]) -> dict:
    headers = {'x-Lizzy-{key}'.format(key=k.title()): v.replace('\n', '\\n')
               for k, v in kwargs.items()}
    headers['X-Lizzy-Version'] = VERSION
    return headers


@decorator
def exception_to_connexion_problem(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except ObjectNotFound as exception:
        problem = connexion.problem(404, 'Not Found',
                                    "Stack not found: {}".format(exception.uid),
                                    headers=_make_headers())
        metrics.count('generic.{}.stack_not_found'.format(func.__name__))
        return problem
    except ExecutionError as error:
        sentry_client.captureException()
        metrics.count('generic.{}.senza_cmd_error'.format(func.__name__))
        return connexion.problem(500,
                                 title='Execution Error',
                                 detail=error.output,
                                 headers=_make_headers())
    except Exception:
        sentry_client.captureException()
        raise


@bouncer
@exception_to_connexion_problem
def all_stacks(references: str=None, region: str=None) -> dict:
    """
    GET /stacks/
    """
    sentry_client.capture_breadcrumb(data={
        'references': references,
        'region': region
    })
    if not references:
        references = []
    stacks = Stack.list(*references, region=region or config.region)
    stacks.sort(key=lambda stack: stack.creation_time)
    metrics.count('get_all_stacks')
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
    region = new_stack.get('region', config.region)  # type: Optional[str]
    dry_run = new_stack.get('dry_run', False)
    tags = new_stack.get('tags', [])
    running_time = MeasureRunningTime('create_stack.success')

    sentry_client.capture_breadcrumb(data={
        'keep_stacks': keep_stacks,
        'new_traffic': new_traffic,
        'stack_version': stack_version,
        'disable_rollback': disable_rollback,
    })

    try:
        senza_definition = yaml.load(senza_yaml)
    except yaml.YAMLError as exception:
        metrics.count('create_stack.invalid_senza_file')
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
        metrics.count('create_stack.missing_stack_name_prop')
        return problem

    # Create the Stack
    logger.info("Creating stack %s...", stack_name)

    senza = Senza(region)
    tags = ['LizzyKeepStacks={}'.format(keep_stacks),
            'LizzyTargetTraffic={}'.format(new_traffic),
            *tags]

    output = senza.create(senza_yaml, stack_version, parameters, disable_rollback,
                          dry_run, tags)

    logger.info("Stack created.", extra={'stack_name': stack_name,
                                         'stack_version': stack_version,
                                         'parameters': parameters})
    stack_dict = (Stack.get(stack_name, stack_version, region=region)
                  if not dry_run
                  else {'stack_name': stack_name,
                        'creation_time': '',
                        'description': '',
                        'status': 'DRY-RUN',
                        'version': stack_version})

    running_time.finish()
    metrics.count('create_stack.region.{}'.format(region))

    return stack_dict, 201, _make_headers(output=output)


@bouncer
@exception_to_connexion_problem
def get_stack(stack_id: str, region: Optional[str]=None) -> dict:
    """
    GET /stacks/{id}
    """
    sentry_client.capture_breadcrumb(data={
        'stack_id': stack_id,
        'region': region,
    })

    stack_name, stack_version = stack_id.rsplit('-', 1)
    stack_dict = Stack.get(stack_name, stack_version, region=region or config.region)
    metrics.count('get_stack')
    return stack_dict, 200, _make_headers()


@bouncer
@exception_to_connexion_problem
def patch_stack(stack_id: str, stack_patch: dict) -> dict:
    """
    PATCH /stacks/{id}

    Update traffic and Taupage image
    """
    sentry_client.capture_breadcrumb(data={
        'stack_id': stack_id,
        'stack_patch': stack_patch,
    })

    stack_patch = filter_empty_values(stack_patch)

    stack_name, stack_version = stack_id.rsplit('-', 1)
    use_region = stack_patch.get('region', config.region)
    senza = Senza(use_region)
    log_info = {'stack_id': stack_id,
                'stack_name': stack_name}
    running_time = MeasureRunningTime('patch_stack.success')

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
    stack_dict = Stack.get(stack_name, stack_version, region=use_region)

    running_time.finish()
    return stack_dict, 202, _make_headers()


@bouncer
@exception_to_connexion_problem
def get_stack_traffic(stack_id: str, region: str=None) -> Tuple[dict, int, dict]:
    """
    GET /stacks/{id}/traffic

    Update traffic and Taupage image
    """
    sentry_client.capture_breadcrumb(data={
        'stack_id': stack_id,
        'region': region,
    })
    stack_name, stack_version = stack_id.rsplit('-', 1)
    senza = Senza(region or config.region)
    running_time = MeasureRunningTime('get_stack_traffic.success')

    traffic_info = senza.traffic(stack_name=stack_name)
    if traffic_info:
        for stack_traffic_info in traffic_info:
            if stack_traffic_info['identifier'] == stack_id:
                return {'weight': float(stack_traffic_info['weight%'])}, 200, _make_headers()

    running_time.finish()
    return connexion.problem(404, 'Not Found',
                             'Stack not found: {}'.format(stack_id),
                             headers=_make_headers())


@bouncer
@exception_to_connexion_problem
def delete_stack(stack_id: str, delete_options: dict) -> dict:
    """
    DELETE /stacks/{id}

    Delete a stack
    """
    sentry_client.capture_breadcrumb(data={
        'stack_id': stack_id,
        'delete_options': delete_options,
    })
    dry_run = delete_options.get('dry_run', False)
    force = delete_options.get('force', False)
    region = delete_options.get('region', config.region)  # type: Optional[str]

    senza = Senza(region)

    logger.info("Removing stack %s...", stack_id)

    running_time = MeasureRunningTime('delete_stack.success')
    output = senza.remove(stack_id,
                          dry_run=dry_run, force=force)
    running_time.finish()

    logger.info("Stack %s removed.", stack_id)
    return '', 204, _make_headers(output=output)


def not_found_path_handler(error):
    return connexion.problem(401, 'Unauthorized', '').flask_response_object()


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
        'config': {
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
