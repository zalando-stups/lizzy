"""
Copyright 2015 Zalando SE

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the
License. You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific
 language governing permissions and limitations under the License.
"""

import datetime
import pytz

import rod.model


class Stack(rod.model.Model):
    prefix = 'lizzy_stack'
    key = 'stack_id'
    search_properties = ['stack_id']

    def __init__(self, *,
                 stack_id: str=None,
                 creation_time: datetime.datetime=None,
                 keep_stacks: int,  # How many stacks to keep
                 traffic: int,  # How much traffic to route to new stack
                 image_version: str,
                 senza_yaml: str,
                 stack_name: str,
                 stack_version: str=None,
                 parameters: list=None,
                 status: str='LIZZY:NEW',
                 **kwargs):
        self.stack_name = stack_name
        self.creation_time = creation_time or datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
        self.image_version = image_version
        self.stack_version = stack_version or self.generate_version(self.creation_time, image_version)
        self.stack_id = stack_id if stack_id is not None else self.generate_id()
        self.keep_stacks = keep_stacks
        self.traffic = traffic
        self.senza_yaml = senza_yaml
        self.parameters = parameters or []
        self.status = status  # status is cloud formation status or LIZZY_NEW

    @staticmethod
    def generate_version(creation_time: datetime.datetime, version: str) -> str:
        version = version.lower().replace('-snapshot', 's').replace('.', 'o')
        return '{version}T{time:%Y%m%d%H%M%S}'.format(version=version, time=creation_time)

    def generate_id(self) -> str:
        """
        The id will be the same as the stack name on aws
        """
        return '{name}-{version}'.format(name=self.stack_name, version=self.stack_version)
