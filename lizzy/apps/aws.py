from datetime import datetime, timedelta
from logging import getLogger

import boto3
from botocore.exceptions import ClientError

from lizzy.exceptions import ObjectNotFound


class AWS(object):

    def __init__(self, region: str):
        super().__init__()
        self.logger = getLogger('lizzy.app.aws')
        self.region = region

    def get_load_balancer_info(self, stack_id: str):
        cf = boto3.client("cloudformation", self.region)
        try:
            response = cf.describe_stack_resource(StackName=stack_id, LogicalResourceId="AppLoadBalancer")
            lb_id = response['StackResourceDetail']['PhysicalResourceId']
            lb_type = response['StackResourceDetail']['ResourceType']
            return lb_id, lb_type
        except ClientError as e:
            msg = e.response.get('Error', {}).get('Message', 'Unknown')
            if all(marker in msg for marker in [stack_id, 'does not exist']):
                raise ObjectNotFound(msg)
            else:
                raise e

    def get_request_count(self, lb_id: str, lb_type: str, minutes: int = 5):
        cw = boto3.client('cloudwatch', self.region)
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
        metrics = cw.get_metric_statistics(**kwargs)
        if len(metrics['Datapoints']) > 0:
            return int(metrics['Datapoints'][0]['Sum'])
        return 0
