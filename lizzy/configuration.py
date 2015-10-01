"""
Copyright 2015 Zalando SE

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the
License. You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific
 language governing permissions and limitations under the License.
"""

import environmental


class Configuration:
    deployer_scope = environmental.Str('DEPLOYER_SCOPE')  # OAUTH scope needed to deploy
    job_interval = environmental.Int('JOB_INTERVAL', 15)  # how many seconds to wait between job runs
    log_format = environmental.Str('LOG_FORMAT', 'json')
    redis_host = environmental.Str('REDIS_HOST', 'localhost')
    redis_port = environmental.Int('REDIS_PORT', 6379)
    region = environmental.Str('REGION', 'eu-west-1')  # AWS Region
    token_url = environmental.Str('TOKEN_URL')
    token_info_url = environmental.Str('TOKEN_INFO_URL')
