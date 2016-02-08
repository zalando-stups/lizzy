.. image:: https://coveralls.io/repos/zalando/lizzy/badge.svg?branch=master&service=github
   :target: https://coveralls.io/github/zalando/lizzy?branch=master

Lizzy
=====

**DISCLAIMER: Lizzy is still in alpha state.**

REST Service to deploy AWS CF templates using Senza.


Configuration
-------------
Lizzy uses the following environment variables for configuration:

+----------------+----------------------------------------+-----------+
| NAME           | DESCRIPTION                            | DEFAULT   |
+================+========================================+===========+
| ALLOWED_USERS  | List of users that can use Lizzy       |           |
+----------------+----------------------------------------+-----------+
| DEPLOYER_SCOPE | OAUTH scope needed to deploy           |           |
+----------------+----------------------------------------+-----------+
| JOB_INTERVAL   | Interval between executions of the job | 15        |
+----------------+----------------------------------------+-----------+
| LOG_LEVEL      | Sets the minimum log level             | INFO      |
+----------------+----------------------------------------+-----------+
| LOG_FORMAT     | Sets the log format (human or default) | default   |
+----------------+----------------------------------------+-----------+
| KIO_URL        | Kio's URL                              |           |
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

Limitations
-----------
Currently Lizzy doesn't support:

- senza definitions with more than one AppServer;
- parameters specified by name;

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
