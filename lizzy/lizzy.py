#!/usr/bin/env python3

# The functions in this module all have `pragma: no cover` because they only setup stuff and don't do "real" work

import apscheduler.schedulers.background as scheduler_background
import apscheduler.triggers.interval as scheduler_interval
import connexion
import rod.connection

import lizzy.configuration as configuration
from lizzy.job import check_status
from lizzy.logging import init_logging

logger = init_logging()


def setup_scheduler(config: configuration.Configuration):  # pragma: no cover
    # configure scheduler
    scheduler = scheduler_background.BackgroundScheduler()
    interval = scheduler_interval.IntervalTrigger(seconds=config.job_interval)
    scheduler.add_job(check_status, interval, max_instances=10, args=[config.region])
    return scheduler


def setup_webapp(config: configuration.Configuration):  # pragma: no cover

    arguments = {'deployer_scope': config.deployer_scope,
                 'token_url': config.token_url,
                 'token_info_url': config.token_info_url}
    logger.debug('Webapp Parameters', extra=arguments)
    app = connexion.App(__name__, config.port, specification_dir='swagger/', server='tornado', arguments=arguments)
    app.add_api('lizzy.yaml')
    return app


def main():  # pragma: no cover
    config = configuration.Configuration()

    logger.info('Connecting to Redis', extra={'redis_host': config.redis_host, 'redis_port': config.redis_port})
    rod.connection.setup(redis_host=config.redis_host, port=config.redis_port)
    logger.info('Connected to Redis')

    logger.info('Starting Scheduler')
    scheduler = setup_scheduler(config)
    scheduler.start()
    logger.info('Scheduler running')

    logger.info('Starting web app')
    app = setup_webapp(config)
    app.run()


if __name__ == '__main__':  # pragma: no cover
    main()
