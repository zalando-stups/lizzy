from _ast import Tuple
from datetime import datetime, timedelta
from logging import getLogger

import boto3
from botocore.exceptions import ClientError

from lizzy.exceptions import ObjectNotFound


class AWS(object):
    """
    Provides convenient access to AWS resources by abstracting and wrapping boto3 calls.
    """
    def __init__(self, region: str):
        super().__init__()
        self.logger = getLogger('lizzy.app.aws')
        self.region = region

    def get_load_balancer_info(self, stack_id: str):
        """
        Resolves the name and type of a stack's load balancer. Raises ObjectNotFound exception if the specified stack
        does not exist or the stack has no load balancer. Useful in combination with get_request_count
        :param stack_id: The stack's id in the format: <stack_name>-<stack_version>
        :return: (load_balancer_name, load_balancer_type)
        """
        cloudformation = boto3.client("cloudformation", self.region)
        try:
            response = cloudformation.describe_stack_resource(StackName=stack_id, LogicalResourceId="AppLoadBalancer")
            lb_id = str(response['StackResourceDetail']['PhysicalResourceId'])
            lb_type = str(response['StackResourceDetail']['ResourceType'])
            return lb_id, lb_type
        except ClientError as error:
            msg = error.response.get('Error', {}).get('Message', 'Unknown')
            if all(marker in msg for marker in [stack_id, 'does not exist']):
                raise ObjectNotFound(msg)
            else:
                raise error

    def get_request_count(self, lb_id: str, lb_type: str, minutes: int = 5) -> int:
        """
        Resolves the request count as reported by AWS Cloudwatch for a given load balancer in the last n minutes.
        Compatible with classic and application load balancers.
        :param lb_id: the id/name of the load balancer
        :param lb_type: either 'AWS::ElasticLoadBalancingV2::LoadBalancer' or 'AWS::ElasticLoadBalancing::LoadBalancer'
        :param minutes: defines the time span to count requests in: now - minutes
        :return: the number of request
        """
        cloudwatch = boto3.client('cloudwatch', self.region)
        end = datetime.utcnow()
        start = end - timedelta(minutes=minutes)
        kwargs = {
            'MetricName': 'RequestCount',
            'StartTime': start,
            'EndTime': end,
            'Period': 60 * minutes,
            'Statistics': ['Sum']
        }
        if lb_type == 'AWS::ElasticLoadBalancingV2::LoadBalancer':
            kwargs.update({
                'Namespace': 'AWS/ApplicationELB',
                'Dimensions': [{
                    'Name': 'LoadBalancer',
                    'Value': lb_id.split('/', 1)[1]
                }]
            })
        elif lb_type == 'AWS::ElasticLoadBalancing::LoadBalancer':
            kwargs.update({
                'Namespace': 'AWS/ELB',
                'Dimensions': [{
                    'Name': 'LoadBalancerName',
                    'Value': lb_id
                }]
            })
        else:
            raise Exception('unknown load balancer type: ' + lb_type)
        metrics = cloudwatch.get_metric_statistics(**kwargs)
        if len(metrics['Datapoints']) > 0:
            return int(metrics['Datapoints'][0]['Sum'])
        return 0
