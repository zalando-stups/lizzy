YAML1 = """
SenzaInfo:
  Parameters:
  - ImageVersion: {Description: Docker image version of lizzy.}
  StackName: lizzy
Test: lizzy:{{Arguments.ImageVersion}}
SenzaComponents:
- Configuration: {Type: 'Senza::StupsAutoConfiguration'}
- AppServer:
    AssociatePublicIpAddress: false
    ElasticLoadBalancer: AppLoadBalancer
    IamRoles: [app-lizzy-bus]
    InstanceType: t2.micro
    SecurityGroups: [app-lizzy-bus]
    TaupageConfig:
      application_version: '{{Arguments.ImageVersion}}'
      health_check_path: /api/swagger.json
      ports: {8080: 8080}
      runtime: Docker
      source: lizzy:{{Arguments.ImageVersion}}
    Type: Senza::TaupageAutoScalingGroup
"""

YAML2 = """
SenzaInfo:
  Parameters:
  - ImageVersion: {Description: Docker image version of lizzy.}
  - Test1:  {Description: test}
  - Test2:  {Description: test}
  StackName: lizzy
Test: lizzy:{{Arguments.ImageVersion}}
Test2: test-{{Arguments.Test1}}
"""

INVALID_YAML = """
- SenzaInfo:
   - Parameters:
     Name: "Something"
"""
