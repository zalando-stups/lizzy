import connexion

from lizzy.models.deployment import Deployment


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
    """
    deployment_dict = {'deployment_id': deployment.deployment_id,
                       'deployment_strategy': deployment.deployment_strategy,
                       'image_version': deployment.image_version,
                       'senza_yaml': deployment.senza_yaml,
                       'stack_name': deployment.stack_name,
                       'stack_version': deployment.stack_version}
    return deployment_dict


def all_deployments() -> dict:
    deployments = [(_get_deployment_dict(deployment)) for deployment in Deployment.all()]
    return {'deployments': deployments}


def new_deployment() -> dict:
    """
    POST /v1.0/deploy/
    """

    deployment = Deployment(**connexion.request.json)
    deployment.save()
    return _get_deployment_dict(deployment)


def deploy(deployment_id: str) -> dict:
    """
    GET /v1.0/deploy/{id}
    """
    deployment = Deployment.get(deployment_id)
    return _get_deployment_dict(deployment)
