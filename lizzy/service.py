#!/usr/bin/env python3

# The functions in this module all have `pragma: no cover` because they only setup stuff and don't do "real" work

import connexion
import logging
import rod.connection
import uwsgi_metrics
import lizzy.configuration as configuration

logger = logging.getLogger('lizzy')


def setup_webapp(config: configuration.Configuration):  # pragma: no cover

    arguments = {'deployer_scope': config.deployer_scope,
                 'token_url': config.token_url}
    logger.debug('Webapp Parameters', extra=arguments)
    app = connexion.App(__name__,
                        specification_dir='swagger/',
                        arguments=arguments,
                        auth_all_paths=True)
    app.add_api('lizzy.yaml')
    return app


def main(run=True):  # pragma: no cover
    config = configuration.Configuration()

    logger.info('Connecting to Redis', extra={'redis_host': config.redis_host, 'redis_port': config.redis_port})
    rod.connection.setup(redis_host=config.redis_host, port=config.redis_port)
    logger.info('Connected to Redis')

    logger.info('Starting web app')
    app = setup_webapp(config)
    # initialization for /metrics endpoint (ZMON support)
    uwsgi_metrics.initialize()
    if run:
        app.run()
    else:
        return app.app


if __name__ == '__main__':  # pragma: no cover
    main()
