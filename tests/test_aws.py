from unittest.mock import MagicMock

import pytest
from botocore.exceptions import ClientError

from lizzy.apps.aws import AWS
from lizzy.exceptions import (ObjectNotFound)


def test_get_load_balancer_info_expired_token(monkeypatch):
    with pytest.raises(ClientError):
        cf = MagicMock()
        cf.describe_stack_resource.side_effect = ClientError(
            {'Error': {
                'Code': 'ExpiredToken',
                'Message': 'The security token included in the request is expired'
            }},
            'DescribeStackResources'
        )
        monkeypatch.setattr('boto3.client', lambda *args, **kwargs: cf)
        aws = AWS('region')
        aws.get_load_balancer_info('stack-id-version')
        cf.describe_stack_resource.assert_called_with(
            **{'StackName': 'stack-id-version', 'LogicalResourceId': 'AppLoadBalancer'}
        )


def test_get_load_balancer_info_stack_not_found(monkeypatch):
    with pytest.raises(ObjectNotFound) as e:
        cf = MagicMock()
        msg = "Stack 'stack-id-version' does not exist"
        cf.describe_stack_resource.side_effect = ClientError(
            {'Error': {
                'Code': 'ValidationError',
                'Message': msg
            }},
            'DescribeStackResources'
        )
        monkeypatch.setattr('boto3.client', lambda *args, **kwargs: cf)
        aws = AWS('region')
        aws.get_load_balancer_info('stack-id-version')
        cf.describe_stack_resource.assert_called_with(
            **{'StackName': 'stack-id-version', 'LogicalResourceId': 'AppLoadBalancer'}
        )
        assert e.uid == msg


def test_get_load_balancer_info_stack_without_load_balancer(monkeypatch):
    with pytest.raises(ObjectNotFound) as e:
        cf = MagicMock()
        msg = "Resource AppLoadBalancer does not exist for stack stack-id-version"
        cf.describe_stack_resource.side_effect = ClientError(
            {'Error': {
                'Code': 'ValidationError',
                'Message': msg
            }},
            'DescribeStackResources'
        )
        monkeypatch.setattr('boto3.client', lambda *args, **kwargs: cf)
        aws = AWS('region')
        aws.get_load_balancer_info('stack-id-version')
        cf.describe_stack_resource.assert_called_with(
            **{'StackName': 'stack-id-version', 'LogicalResourceId': 'AppLoadBalancer'}
        )
        assert e.uid == msg


def test_get_load_balancer_info_happy_path(monkeypatch):
    cf = MagicMock()
    cf.describe_stack_resource.return_value = {
        'StackResourceDetail': {
            'PhysicalResourceId': 'lb-id',
            'ResourceType': 'lb-type'
        }
    }
    monkeypatch.setattr('boto3.client', lambda *args, **kwargs: cf)
    aws = AWS('region')
    lb_id, lb_type = aws.get_load_balancer_info('stack-id-version')
    cf.describe_stack_resource.assert_called_with(
        **{'StackName': 'stack-id-version', 'LogicalResourceId': 'AppLoadBalancer'}
    )
    assert lb_id == 'lb-id'
    assert lb_type == 'lb-type'


def test_get_request_count_invalid_lb_type():
    aws = AWS('region')
    with pytest.raises(Exception) as e:
        aws.get_request_count('lb-id', 'invalid-lb-type')
        assert e.msg == 'unknown load balancer type: invalid-lb-type'


@pytest.mark.parametrize(
    'elb_name, elb_type, response, expected_result',
    [
        ('lb_name', 'AWS::ElasticLoadBalancing::LoadBalancer', {'Datapoints': [{'Sum': 4176}]}, 4176),
        ('lb_name', 'AWS::ElasticLoadBalancing::LoadBalancer', {'Datapoints': []}, 0),
        ('arn:aws:cf:region:account:stack/stack-id-version/uuid', 'AWS::ElasticLoadBalancingV2::LoadBalancer',
         {'Datapoints': [{'Sum': 94374}]}, 94374),
        ('arn:aws:cf:region:account:stack/stack-id-version/uuid', 'AWS::ElasticLoadBalancingV2::LoadBalancer',
         {'Datapoints': []}, 0),
    ])
def test_get_load_balancer_with_classic_lb_sum_present(monkeypatch, elb_name, elb_type, response, expected_result):
    cw = MagicMock()
    cw.get_metric_statistics.return_value = response
    monkeypatch.setattr('boto3.client', lambda *args, **kwargs: cw)
    aws = AWS('region')
    request_count = aws.get_request_count(elb_name, elb_type)
    assert request_count == expected_result
