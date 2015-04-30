#!/usr/bin/env python3

import logging

import apscheduler.schedulers.background as scheduler_background
import apscheduler.jobstores.redis as redis_jobstore
import apscheduler.triggers.interval as scheduler_interval
import connexion
import flask
import rod.connection


PORT = 9000

root_logger = logging.getLogger('lizzy')
logging.basicConfig(level=logging.DEBUG)


request = flask.request


def check_status():
    logger = logging.getLogger('lizzy.job')
    logger.debug('In Job')

# configure scheduler
redis_jobstore.RedisJobStore()
scheduler = scheduler_background.BackgroundScheduler()
every_10_seconds = scheduler_interval.IntervalTrigger(seconds=10)
scheduler.add_job(check_status, every_10_seconds)

# configure app
swagger_app = connexion.App(__name__, PORT, specification_dir='swagger/')
swagger_app.add_api('lizzy.v1.yaml')



def main():
    # TODO make redis configurable
    root_logger.info('Connecting to Redis')
    rod.connection.setup(redis_host='localhost', port=6379)

    root_logger.info('Starting Scheduler')
    scheduler.start()
    root_logger.info('Scheduler running')

    root_logger.info('Starting web app')
    swagger_app.run()

if __name__ == '__main__':
    main()