import json
import connexion

from lizzy.models.deployment import Deployment


def all_deployments() -> dict:
    deployments = [deployment.as_dict() for deployment in Deployment.all()]
    return {'deployments': deployments}

def new_deployment() -> dict:
    """
    POST /v1.0/deploy/
    """

    deployment = Deployment(**connexion.request.json)
    deployment.save()
    return deployment.as_dict()


def deploy(deployment_id: str) -> dict:
    """
    GET /v1.0/deploy/{id}
    """
    deployment = Deployment.get(deployment_id)
    return deployment.as_dict()