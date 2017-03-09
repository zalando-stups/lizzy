.. image:: https://coveralls.io/repos/zalando/lizzy/badge.svg?branch=master&service=github
   :target: https://coveralls.io/github/zalando/lizzy?branch=master


=====
Lizzy
=====

Lizzy is a wrapper around `Senza`_: a command line deployment tool for
creating and executing AWS `CloudFormation`_ templates. With Lizzy,
autonomous teams can use `Senza`_, within their `continuous delivery`_
pipelines, to deploy new versions of their apps to a team-specific AWS
account. Lizzy can be deployed to an AWS account, then it's REST API
can be used to deploy new apps to that account.


Why Lizzy
=========

At `Zalando`_, development teams have their own AWS accounts so they
can work autonomously. One team (Continuous Delivery) is responsible
for maintaining the `Jenkinses`_ of all other Zalando teams. This allows
teams to focus on their `OKR's`_ instead of spending their time
configuring `Jenkins`_ or creating their own continuous deployment
tools. For Zalando, Lizzy helps make `continuous delivery`_ using our
Jenkins-as-a-Service setup possible. Without Lizzy teams would need
to save AWS credentials to their Jenkins instance.

If your team is interested in working with `immutable stacks`_ on AWS
you can use `Senza`_ to create and manage your stacks using
`CloudFormation`_. Lizzy is an additional tool that provides a
deployment API to be used by your `continuous delivery`_ pipeline to
run Senza commands. Lizzy can be used along with any code integration
tool like `Jenkins`_, `TravisCI`_, `CircleCI`_, etc.


How Lizzy Works
===============

Lizzy consists of the Lizzy Agent — a REST API service — and the
`Lizzy-Client`_ command line tool.

The Lizzy Agent is a web application deployed in a team's AWS account
and granted access to create new CloudFormation stacks through a REST
API. All requests are authenticated using `OAuth2`_ bearer tokens.

`Lizzy-Client`_ mimics the usage of `Senza`_'s commands and transforms
them into HTTP requests, which are then sent to Lizzy Agent's REST
API.


Who Uses Lizzy
==============

Many Zalando teams use Lizzy in production to deliver high-quality
services that power the `fastest-growing`_ online fashion platform in
Europe. If you want to know more about how Zalando uses Lizzy, please
read our blog post `Continuous Delivery pipelines of ghe-backups with
Lizzy`_.


How to Run Lizzy Locally
========================

This repository includes a `Dockerfile`_ that you can use to build an
image locally using the command:

.. code-block:: sh

    $ docker build -t lizzy:dev .


.. hint:: If you clone this repository, the "scm-source.json" file
          will be missing. To know more about what is in this file,
          please read the `STUPS documentation`_. We have `tools`_
          that can generate this file for you.

After the image is built, it will be available with the tag
"lizzy:dev". You will also need to specify some environment variables
for Lizzy to use. Here is an "example.cfg" file:

.. code-block:: cfg

    TOKEN_URL=https://token.auth.example.com/oauth2/access_token
    TOKENINFO_URL=https://info.auth.example.com/oauth2/tokeninfo
    ALLOWED_USERS=['robotusername','myusername']
    DEPLOYER_SCOPE=deployer
    LOG_LEVEL=DEBUG

You also need to configure the `AWS credentials`_ locally in your
machine under `~/.aws`. After that, you can run the Lizzy image with
the command:

.. code-block:: sh

    $ docker run --rm -p 8080:8080 --env-file environment.cfg -v ~/.aws:/.aws --name lizzy -u 999 -it lizzy:dev

The application will be available by default at the port `8080`, which
is usually accessible at `http://127.0.0.1:8080`. It depends on how
you've configured Docker locally. A `Swagger/OpenAPI console`_ is
available at `http://127.0.0.1:8080/api/ui/#/default`.


Deploying to AWS
================

There are many ways to deploy Lizzy to AWS. At Zalando we use
`STUPS`_, which provides a convenient and audit-compliant
Platform-as-a-Service (PaaS). An example of the `Senza definition`_ to
deploy Lizzy:

.. code-block:: yaml

    SenzaInfo:
      StackName: lizzy
      Parameters:
        - ImageVersion:
            Description: "Docker image version of lizzy."
    SenzaComponents:
      - Configuration:
          Type: 'Senza::StupsAutoConfiguration'
      - AppServer:
          Type: Senza::TaupageAutoScalingGroup
          AssociatePublicIpAddress: false
          ElasticLoadBalancer: AppLoadBalancer
          IamRoles: ['app-lizzy']
          InstanceType: t2.nano
          SecurityGroups: ['app-lizzy']
          TaupageConfig:
            application_version: '{{Arguments.ImageVersion}}'
            environment:
              ALLOWED_USER_PATTERN: "^(jenkins-slave-\\w+)$"
              DEPLOYER_SCOPE: myscope
              LANG: C.UTF-8
              LC_ALL: C.UTF-8
              LOG_LEVEL: DEBUG
              REGION: '{{AccountInfo.Region}}'
              TOKEN_URL: 'https://token.auth.example.com/oauth2/access_token'
              TOKENINFO_URL: 'https://info.auth.example.com/oauth2/tokeninfo'
            health_check_path: /api/swagger.json
            ports: {8080: 8080}
            runtime: Docker
            source: 'lizzy:{{Arguments.ImageVersion}}'
      - AppLoadBalancer:
          HTTPPort: 8080
          HealthCheckPath: /api/swagger.json
          Scheme: internet-facing
          SecurityGroups: ['app-lizzy-lb']
          Type: Senza::WeightedDnsElasticLoadBalancer


Access Control for Lizzy
------------------------

To create new CloudFormation stacks, Lizzy applications need access to
CloudFormation plus some other services from Amazon's API. You will
need to specify the `IAM role`_ in a manner like:

.. code-block:: json

    {
        "Statement": [
            {
                "Action": [
                    "iam:*",
                    "cloudformation:*",
                    "ec2:*",
                    "route53:*",
                    "elasticloadbalancing:*",
                    "cloudwatch:*",
                    "elasticache:*",
                    "acm:*",
                    "autoscaling:*",
                    "sqs:*"
                ],
                "Effect": "Allow",
                "Resource": "*"
            }
        ],
        "Version": "2012-10-17"
    }

That is the minimal configuration Lizzy needs to run Senza commands
successfully. Other statements might be included in this configuration.


Configuration
=============

Lizzy uses the following environment variables for configuration:

+----------------------+----------------------------------------+-----------+
| NAME                 | DESCRIPTION                            | DEFAULT   |
+======================+========================================+===========+
| ALLOWED_USERS        | List of users that can use Lizzy       |           |
+----------------------+----------------------------------------+-----------+
| ALLOWED_USER_PATTERN | Defines a regular expression to match  |           |
|                      | usernames allowed to use Lizzy         |           |
+----------------------+----------------------------------------+-----------+
| DEPLOYER_SCOPE       | OAUTH scope needed to deploy           |           |
+----------------------+----------------------------------------+-----------+
| LOG_LEVEL            | Sets the minimum log level             | INFO      |
+----------------------+----------------------------------------+-----------+
| LOG_FORMAT           | Sets the log format (human or default) | default   |
+----------------------+----------------------------------------+-----------+
| REGION               | AWS Region to use                      | eu-west-1 |
+----------------------+----------------------------------------+-----------+
| SENTRY_DSN           | Sentry URL with client keys            |           |
+----------------------+----------------------------------------+-----------+
| TOKEN_URL            | URL to get a new token                 |           |
+----------------------+----------------------------------------+-----------+
| TOKENINFO_URL        | URL to validate the token              |           |
+----------------------+----------------------------------------+-----------+

Configuring Access to Lizzy
---------------------------

There are two environment variables for configuring who is allowed to
perform successful calls to the Lizzy Agent. You must use one (and
ONLY one) of them: Either `ALLOWED_USERS` or
`ALLOWED_USER_PATTERN`. To choose which one fits your use case, you
first need to understand what they do.

- **ALLOWED_USERS**: List of specific usernames that can access
  Lizzy. Use it when you know the exact usernames of the clients you
  want to give access to your service.
- **ALLOWED_USER_PATTERN**: Regular expression that should match the
  username of the clients that are going to call the Lizzy API. Use it
  when you know that the username should start with some pattern, like
  `stups_.+`.

Those variables are mutually exclusive. Again: use only one of them.


Authentication Service
----------------------

The **TOKEN_URL** environment variable should point to the service
that provides OAuth tokens. At Zalando, we use the open-source `PlanB
provider`_ for that. The **TOKENINFO_URL** environment variable should
point to the service that stores information about the tokens. To
store the OAuth2 token information, we use `PlanB token info`_, also
developed by Zalando. If you do not have any OAuth2 infrastructure,
please take a look at those projects.

Contributing to Lizzy
=====================

We welcome your ideas, issues, and pull requests. Just follow the
usual/standard `GitHub practices`_.

License
=======
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

.. _Senza: https://github.com/zalando-stups/senza
.. _OKR's: https://en.wikipedia.org/wiki/OKR
.. _Lizzy-Client: https://github.com/zalando/lizzy-client
.. _Zalando: https://www.zalando.com
.. _`fastest-growing`: https://www.fbicgroup.com/sites/default/files/Europes%2025%20Fastest-Growing%20Major%20Apparel%20Retailers.pdf
.. _`Continuous Delivery pipelines of ghe-backups with Lizzy`: https://tech.zalando.de/blog/ci-pipelines-with-lizzy/
.. _`AWS credentials`: http://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html
.. _`PlanB provider`: https://github.com/zalando/planb-provider
.. _`PlanB token info`: https://github.com/zalando/planb-tokeninfo
.. _`GitHub practices`: https://guides.github.com/introduction/flow/
.. _`OAuth2`: http://planb.readthedocs.io/en/latest/oauth2.html
.. _`Dockerfile`: https://github.com/zalando/lizzy/blob/master/Dockerfile
.. _`STUPS`: http://stups.readthedocs.io/en/latest/
.. _`STUPS documentation`: http://stups.readthedocs.io/en/latest/user-guide/application-development.html#scm-source-json
.. _`tools`: https://github.com/zalando-stups/python-scm-source
.. _`Senza definition`: https://github.com/zalando-stups/senza#senza-definition
.. _`IAM role`: http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/iam-roles-for-amazon-ec2.html
.. _`continuous delivery`: https://en.wikipedia.org/wiki/Continuous_delivery
.. _`Swagger/OpenAPI console`: http://swagger.io/
.. _`CloudFormation`: https://aws.amazon.com/cloudformation/
.. _`immutable stacks`: http://thenewstack.io/a-brief-look-at-immutable-infrastructure-and-why-it-is-such-a-quest/
.. _`Jenkinses`: https://jenkins.io/
.. _`Jenkins`: https://jenkins.io/
.. _`TravisCI`: https://travis-ci.org/
.. _`CircleCI`: https://circleci.com/
