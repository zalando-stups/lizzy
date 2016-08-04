#!/usr/bin/env python3

# The functions in this module all have `pragma: no cover` because they only
# setup stuff and don't do "real" work

import logging

import connexion
import werkzeug.exceptions

from lizzy.api import not_found_path_handler, expose_api_schema, health_check
from .serialization import JSONEncoder
import lizzy.configuration as configuration

logger = logging.getLogger('lizzy')  # pylint: disable=invalid-name


def setup_webapp(config: configuration.Configuration):  # pragma: no cover

    arguments = {'deployer_scope': config.deployer_scope,
                 'token_url': config.token_url}
    logger.debug('Webapp Parameters', extra=arguments)
    app = connexion.App(__name__,
                        specification_dir='swagger/',
                        arguments=arguments,
                        auth_all_paths=True)
    app.add_api('lizzy.yaml')

    flask_app = app.app
    flask_app.json_encoder = JSONEncoder

    flask_app.register_error_handler(werkzeug.exceptions.NotFound,
                                     not_found_path_handler)

    flask_app.add_url_rule('/.well-known/schema-discovery',
                           'schema_discovery_endpoint',
                           expose_api_schema)

    flask_app.add_url_rule('/health',
                           'health_check_endpoint',
                           health_check)

    return app


def main(run=True):  # pragma: no cover
    config = configuration.Configuration()

    logger.info('Starting web app')
    app = setup_webapp(config)
    if run:
        app.run()
    else:
        return app.app


if __name__ == '__main__':  # pragma: no cover
    main()
