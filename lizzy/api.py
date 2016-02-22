from typing import Optional  # noqa
from decorator import decorator
import logging
import connexion
import yaml

from lizzy import config
from lizzy.apps.kio import Kio
from lizzy.apps.senza import Senza
from lizzy.models.stack import Stack
from lizzy.security import bouncer
from lizzy.version import VERSION
from lizzy.exceptions import ObjectNotFound, AIMImageNotUpdated
from lizzy.deployer import InstantDeployer
from lizzy.util import filter_empty_values


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
    stacks = [(_get_stack_dict(stack)) for stack in Stack.all()]
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

    try:
        senza_definition = yaml.safe_load(senza_yaml)
        if not isinstance(senza_definition, dict):
            raise TypeError
    except yaml.YAMLError:
        logger.exception("Couldn't parse senza yaml.",
                         extra={'senza_yaml': repr(senza_yaml)})
        return connexion.problem(400,
                                 'Invalid senza yaml',
                                 "Failed to parse senza yaml.",
                                 headers=_make_headers())
    except TypeError:
        logger.exception("Senza yaml is not a dict.",
                         extra={'senza_yaml': repr(senza_yaml)})
        return connexion.problem(400,
                                 'Invalid senza yaml',
                                 "Senza yaml is not a dict.",
                                 headers=_make_headers())

    try:
        stack_name = senza_definition['SenzaInfo']['StackName']  # type: str
        # TODO validate stack name
    except KeyError as exception:
        logger.error("Couldn't get stack name from definition.",
                     extra={'senza_yaml': repr(senza_definition)})
        missing_property = str(exception)
        problem = connexion.problem(400,
                                    'Invalid senza yaml',
                                    "Missing property in senza yaml: {}".format(missing_property),
                                    headers=_make_headers())
        return problem

    # Create the Stack
    logger.info("Creating stack %s...", stack_name)
    stack = Stack(keep_stacks=keep_stacks,
                  traffic=new_traffic,
                  image_version=image_version,
                  senza_yaml=senza_yaml,
                  stack_name=stack_name,
                  stack_version=stack_version,
                  application_version=application_version,
                  parameters=parameters)
    definition = stack.generate_definition()
    if stack.application_version:
        kio_extra = {'stack_name': stack_name, 'version': application_version}
        logger.info("Registering version on kio...", extra=kio_extra)
        taupage_config = definition.app_server.get('TaupageConfig', {})  # type: Dict[str, str]
        artifact_name = taupage_config.get('source', '')
        kio = Kio()
        if kio.versions_create(stack.stack_name, stack.stack_version, artifact_name):
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
        stack.status = 'LIZZY:DEPLOYING'
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

    if 'new_aim_image' in stack_patch:
        new_aim_image = stack_patch['new_aim_image']
        try:
            deployer.update_aim_image(new_aim_image)
            stack.aim_image = new_aim_image
        except AIMImageNotUpdated as e:
            return connexion.problem(400, 'Image update failed', e.message,
                                     headers=_make_headers())

    stack.traffic = stack_patch.get('new_traffic', stack.traffic)  # type: int
    stack.status = 'LIZZY:CHANGE'
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
        stack.status = 'LIZZY:DELETE'
        stack.save()
    return '', 204, _make_headers()
