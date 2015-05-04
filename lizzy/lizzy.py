#!/usr/bin/env python3

import logging

import apscheduler.schedulers.background as scheduler_background
import apscheduler.triggers.interval as scheduler_interval
import connexion
import rod.connection

import lizzy.jobs

PORT = 9000

logger = logging.getLogger('lizzy')
logging.basicConfig(level=logging.DEBUG)

# configure scheduler
scheduler = scheduler_background.BackgroundScheduler()
interval = scheduler_interval.IntervalTrigger(seconds=60)  # Todo Make this time small for live
scheduler.add_job(lizzy.jobs.check_status, interval, max_instances=10)

# configure app
swagger_app = connexion.App(__name__, PORT, specification_dir='swagger/')
swagger_app.add_api('lizzy.v1.yaml')


def main():
    # TODO make redis configurable
    logger.info('Connecting to Redis')
    rod.connection.setup(redis_host='localhost', port=6379)
    logger.info('Connected to Redis')

    logger.info('Starting Scheduler')
    scheduler.start()
    logger.info('Scheduler running')

    logger.info('Starting web app')
    swagger_app.run()

if __name__ == '__main__':
    main()
