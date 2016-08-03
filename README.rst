.. image:: https://coveralls.io/repos/zalando/lizzy/badge.svg?branch=master&service=github
   :target: https://coveralls.io/github/zalando/lizzy?branch=master

=====
Lizzy
=====

Lizzy is a wrapper around `Senza`_ (a command line deployment tool to
create and execute AWS CloudFormation templates) that allows cross
AWS accounts deployments.

Why Lizzy?
==========

Lizzy was created with the objective of enabling autonomous teams at
`Zalando`_ to use Jenkins pipelines to continuously deploy new versions of
their apps to their AWS accounts using the `Senza`_ CLI tool.

The managed Jenkinses at Zalando run under the Continuous Delivery team's
AWS account. The Continuous Delivery team is responsible for
maintaining the Jenkinses of all other Zalando teams. That allows
other teams in the company to focus on their `OKR's`_ and not invest
their time on configuring Jenkins or continuous deployment tools. The
teams at Zalando enjoy `Jenkins-as-a-Service`_.

Each team at Zalando has their own AWS account. So running the
`Senza`_ tool within a managed Jenkins job would allow deployments only in
the Continuous Delivery team's AWS account. To permit different teams
to deploy in their own AWS account Lizzy was created.

How Lizzy works?
================

Lizzy consists of a REST API service (also called Agent) and the
`Lizzy-Client`_ tool.

The Lizzy Agent is a web application that is deployed in the team's
account and granted access to create new Cloud Formation stacks. All
requests are expected to be authenticated using `OAuth2`_ Bearer Tokens.

The `Lizzy-Client`_ is a command line tool that mimics the usage of
the original `Senza`_ tool commands and transforms those commands to HTTP
requests sent to the REST API of Lizzy Agent.

Who is using Lizzy?
===================

Lizzy is being used in production at Zalando to delivery high quality
services to power the `fastest growing`_ online fashion
retailer store in Europe. If you want to know more about how Lizzy is
used at Zalando please take a look at our blog post
`Continuous Delivery pipelines of ghe-backups with Lizzy`_.

How to run Lizzy locally?
=========================

We provide in this repository a `Dockerfile`_ which you can use to
build an image locally using the command:

.. code-block:: sh

    $ docker build -t lizzy:dev .


.. hint:: The "scm-source.json" file will be missing if you just clone
          this repository. To know more what is this file, please read
          the `STUPS documentation`_. We have `tools`_ that can generate
          this file for you.

After the image build, it will be available within the tag
"lizzy:dev". You will also need to specify some environment
variables to be used by Lizzy. Here is an "example.cfg" file:

.. code-block:: cfg

    TOKEN_URL=https://token.auth.example.com/oauth2/access_token
    TOKENINFO_URL=https://info.auth.example.com/oauth2/tokeninfo
    ALLOWED_USERS=['robotusername','myusername']
    DEPLOYER_SCOPE=deployer
    LOG_LEVEL=DEBUG

It is also necessary to configure the `AWS credentials`_ locally in
your machine under `~/.aws`. After that you can run the Lizzy image
with the command:

.. code-block:: sh

    $ docker run --rm -p 8080:8080 --env-file environment.cfg -v ~/.aws:/.aws --name lizzy -u 999 -it lizzy:dev

The application by default will be listening on port `8080`. Usually
accessible at `http://127.0.0.1:8080`, it depends on how your Docker is
configured locally. A Swagger/OpenAPI console will be available at
`http://127.0.0.1:8080/api/ui/#/default`.

Deploying to AWS
================

There are many ways to deploy Lizzy to AWS. At Zalando we use `STUPS
platform`_ that provides a convenient and audit-compliant
Platform-as-a-Service (PaaS). An example of the `Senza definition`_ to
deploy Lizzy would be:

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

Lizzy application will need to have access to create new Cloud
Formation stacks and some others services from Amazon API. You will
need to specify the a `IAM role`_ similar to:

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
                    "autoscaling:*"
                ],
                "Effect": "Allow",
                "Resource": "*"
            }
        ],
        "Version": "2012-10-17"
    }

That is the minimal configuration needed for Lizzy to be able to run
successfully Senza commands. Other statements might be included in this

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
| TOKEN_URL            | URL to get a new token                 |           |
+----------------------+----------------------------------------+-----------+
| TOKENINFO_URL        | URL to validate the token              |           |
+----------------------+----------------------------------------+-----------+

Configuring access to Lizzy
---------------------------

Two environment variables are used to configure who is allowed to
perform successful calls to Lizzy Agent. One and only one of them must
be used (`ALLOWED_USERS` and `ALLOWED_USER_PATTERN`). To choose which
one fits better to your use case you need to understand what they do.

- **ALLOWED_USERS**: List of specific usernames that can access
  Lizzy. Used when you know exactly what are the usernames of the
  clients you want to access your service.
- **ALLOWED_USER_PATTERN**: Regular expression that should match with
  the username of the clients that are going to call the Lizzy
  API. Used when you know that the username should start with some
  pattern like `stups_.+`.

Those variables are mutually exclusives and you should use only one
of them.

Authentication Service
----------------------

The **TOKEN_URL** environment variable should point to the service
that provides OAuth tokens. At Zalando we use `PlanB provider`_ for
that. The **TOKENINFO_URL** environment variable should point to the
service stores information about the tokens. To store the OAuth2 token
information we use another Open Source project `PlanB token info`_
also developed by Zalando. If you do not have any OAuth2
infrastructure, please take a look at those projects.

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
.. _`fastest growing`: https://www.fbicgroup.com/sites/default/files/Europes%2025%20Fastest-Growing%20Major%20Apparel%20Retailers.pdf
.. _`Continuous Delivery pipelines of ghe-backups with Lizzy`: https://tech.zalando.de/blog/ci-pipelines-with-lizzy/
.. _`AWS credentials`: http://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html
.. _`PlanB provider`: https://github.com/zalando/planb-provider
.. _`PlanB token info`: https://github.com/zalando/planb-tokeninfo
.. _`GitHub practices`: https://guides.github.com/introduction/flow/
.. _`Jenkins-as-a-Service`: https://github.com/zalando/zalando-rules-of-play#continuous-delivery
.. _`OAuth2`: http://planb.readthedocs.io/en/latest/oauth2.html
.. _`Dockerfile`: https://github.com/zalando/lizzy/blob/master/Dockerfile
.. _`STUPS platform`: http://stups.readthedocs.io/en/latest/
.. _`STUPS documentation`: http://stups.readthedocs.io/en/latest/user-guide/application-development.html#scm-source-json
.. _`tools`: https://github.com/zalando-stups/python-scm-source
.. _`Senza definition`: https://github.com/zalando-stups/senza#senza-definition
.. _`IAM role`: http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/iam-roles-for-amazon-ec2.html
