import connexion
import decorator

from lizzy import Configuration
from lizzy.api import logger


@decorator.decorator
def bouncer(endpoint, *args, **kwargs):
    config = Configuration()
    if config.allowed_users is not None:
        logger.debug('Checking if user is allowed',
                     extra={'user': connexion.request.user, 'allowed_users': config.allowed_users})
        if connexion.request.user not in config.allowed_users:
            return connexion.problem(403, 'Forbidden', "User is not allowed to access this endpoint")
    return endpoint(*args, **kwargs)
