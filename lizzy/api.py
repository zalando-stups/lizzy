"""
Copyright 2015 Zalando SE

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the
License. You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific
 language governing permissions and limitations under the License.
"""

import logging

import connexion
import yaml

from lizzy.models.deployment import Deployment


logger = logging.getLogger('lizzy.api')


def _get_deployment_dict(deployment: Deployment) -> dict:
    """
    From lizzy.v1.yaml:
      deployment_id:
        type: string
        description: Unique ID for the deployment
      deployment_strategy:
        type: string
        description: Deployment strategy
      image_version:
        type: string
        description: Docker image version to deploy
      senza_yaml:
        type: string
        description: YAML to provide to senza
      stack_name:
        type: string
        description: Cloud formation stack name prefix
      status:
        type: string
        description: Cloud formation stack status
    """
    deployment_dict = {'deployment_id': deployment.deployment_id,
                       'deployment_strategy': deployment.deployment_strategy,
                       'image_version': deployment.image_version,
                       'senza_yaml': deployment.senza_yaml,
                       'stack_name': deployment.stack_name,
                       'stack_version': deployment.stack_version,
                       'status': deployment.status}
    return deployment_dict


def all_deployments() -> dict:
    deployments = [(_get_deployment_dict(deployment)) for deployment in Deployment.all()]
    return {'deployments': deployments}


def new_deployment() -> dict:
    """
    POST /v1.0/deploy/
    """

    try:
        deployment_strategy = connexion.request.json['deployment_strategy']
        image_version = connexion.request.json['image_version']
        senza_yaml = connexion.request.json['senza_yaml']
    except KeyError as e:
        missing_property = str(e)
        logger.error("Missing property on request: %s", missing_property)
        raise connexion.exceptions.BadRequest("Missing property: {}".format(missing_property))

    try:
        senza_definition = yaml.safe_load(senza_yaml)
        if not isinstance(senza_definition, dict):
            raise TypeError
    except yaml.YAMLError:
        logger.exception("Couldn't parse senza yaml:\n %s", senza_yaml)
        raise connexion.exceptions.BadRequest("Invalid senza yaml")
    except TypeError:
        logger.exception("Senza yaml is not a dict:\n %s", senza_yaml)
        raise connexion.exceptions.BadRequest("Invalid senza yaml")

    try:
        stack_name = senza_definition['SenzaInfo']['StackName']
        # TODO validate stack name
    except KeyError as e:
        logger.error("Couldn't get stack name for:\n%s", senza_yaml)
        missing_property = str(e)
        raise connexion.exceptions.BadRequest("Missing property in senza yaml: {}".format(missing_property))

    deployment = Deployment(deployment_strategy=deployment_strategy,
                            image_version=image_version,
                            senza_yaml=senza_yaml,
                            stack_name=stack_name)
    deployment.save()
    return _get_deployment_dict(deployment)


def deploy(deployment_id: str) -> dict:
    """
    GET /v1.0/deploy/{id}
    """
    deployment = Deployment.get(deployment_id)
    return _get_deployment_dict(deployment)
