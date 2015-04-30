import logging

import lizzy.models.deployment

logger = logging.getLogger('lizzy.job')


def check_status():
    all_deployments = lizzy.models.deployment.Deployment.all()
    logger.debug('In Job')
    for deployment in all_deployments:
        if deployment.lock(5000):
            logger.debug('ID: %s, STATUS: %s', deployment.deployment_id, deployment.status)
        else:
            logger.debug('Deployment object was locked skipping')
