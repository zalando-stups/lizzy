import connexion
import decorator
import logging

from lizzy import Configuration

logger = logging.getLogger('lizzy.security')


@decorator.decorator
def bouncer(endpoint, *args, **kwargs):
    """
    Checks if the user making request is in the predefined list of allowed users
    """
    config = Configuration()

    if not hasattr(connexion.request, 'user'):
        logger.debug('User not found in the request',
                     extra={'allowed_users': config.allowed_users})
        return connexion.problem(403, 'Forbidden', "Anonymous access is not allowed in this endpoint")

    if config.allowed_users is not None:
        logger.debug('Checking if user is allowed',
                     extra={'user': connexion.request.user, 'allowed_users': config.allowed_users})
        if connexion.request.user not in config.allowed_users:
            return connexion.problem(403, 'Forbidden', "User is not allowed to access this endpoint")

    return endpoint(*args, **kwargs)
