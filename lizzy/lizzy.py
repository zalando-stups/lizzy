#!/usr/bin/env python3

"""
Copyright 2015 Zalando SE

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the
License. You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific
 language governing permissions and limitations under the License.
"""

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
interval = scheduler_interval.IntervalTrigger(seconds=5)  # Todo Make this configurable
scheduler.add_job(lizzy.jobs.check_status, interval, max_instances=10)

# configure app
swagger_app = connexion.App(__name__, PORT, specification_dir='swagger/')
swagger_app.add_api('lizzy.yaml')


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
