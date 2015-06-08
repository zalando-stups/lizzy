Lizzy
=====

REST Service to deploy AWS CF templates using Senza

Configuration
-------------
Lizzy uses the following environment variables for configuration:

+----------------+----------------------------------------+-----------+
| NAME           | DESCRIPTION                            | DEFAULT   |
+================+========================================+===========+
| JOB_INTERVAL   | Interval between executions of the job | 15        |
+----------------+----------------------------------------+-----------+
| PORT           | TCP port to use for lizzy              | 8080      |
+----------------+----------------------------------------+-----------+
| REDIS_HOST     | Hostname of the Redis Server           | localhost |
+----------------+----------------------------------------+-----------+
| REDIS_PORT     | Port of the Redis Server               | 6379      |
+----------------+----------------------------------------+-----------+
| REGION         | AWS Region to use                      | eu-west-1 |
+----------------+----------------------------------------+-----------+
| TOKEN_URL      | URL to get a new token                 |           |
+----------------+----------------------------------------+-----------+
| TOKEN_INFO_URL | URL to validate the token              |           |
+----------------+----------------------------------------+-----------+

License
-------
Copyright 2015 Zalando SE

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.