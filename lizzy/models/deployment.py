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
import datetime
import random

import rod.model


logger = logging.getLogger('lizzy.model.deployment')


class Deployment(rod.model.Model):

    prefix = 'lizzy_deployment'
    key = 'deployment_id'
    search_properties = ['deployment_id']

    def __init__(self, *,
                 deployment_id: str=None,
                 keep_stacks: int,  # How many stacks to keep
                 new_trafic: int,  # How much traffic to route to new stack
                 image_version: str,
                 senza_yaml: str,
                 stack_name: str,
                 stack_version: str=None,
                 status: str='LIZZY:NEW',
                 **kwargs):
        self.stack_name = stack_name
        self.stack_version = stack_version if stack_version is not None else self.generate_version()
        self.deployment_id = deployment_id if deployment_id is not None else self.generate_id()
        self.keep_stacks = keep_stacks
        self.new_trafic = new_trafic
        self.image_version = image_version
        self.senza_yaml = senza_yaml
        self.status = status  # status is cloud formation status or LIZZY_NEW

    @staticmethod
    def generate_version() -> str:
        now = datetime.datetime.utcnow()
        random_part = random.randint(0, 255)
        return '{time:%y%m%d%H%M%S}{rand:02x}'.format(time=now, rand=random_part)

    def generate_id(self) -> str:
        """
        The id will be the same as the stack name on aws
        """
        return '{name}-{version}'.format(name=self.stack_name, version=self.stack_version)
