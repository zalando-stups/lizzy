GOOD_CF_DEFINITION = {
    "AWSTemplateFormatVersion": "2010-09-09",
    "Mappings": {
        "Senza": {
            "Info": {
                "StackName": "abc",
                "StackVersion": "2"
            }
        }
    },
    "Parameters": {},
    "Resources": {
        "AppServerConfig": {
            "Properties": {
                "ImageId": "image-id",
                "InstanceType": "t2.micro",
                "UserData": {
                    "Fn::Base64": "#taupage-config\napplication_id: abc\nsource: pierone.example.com/lizzy/lizzy:12\n"
                }
            },
            "Type": "AWS::AutoScaling::LaunchConfiguration"
        }
    }
}

GOOD_CF_DEF_WITH_DIFFERENT_APPLICATION_ID = {
    "AWSTemplateFormatVersion": "2010-09-09",
    "Mappings": {
        "Senza": {
            "Info": {
                "StackName": "abc-stackname",
                "StackVersion": "2"
            }
        }
    },
    "Parameters": {},
    "Resources": {
        "AppServerConfig": {
            "Properties": {
                "ImageId": "image-id",
                "InstanceType": "t2.micro",
                "UserData": {
                    "Fn::Base64": "#taupage-config\napplication_id: abc-specific-id\nsource: pierone.example.com/lizzy/lizzy:12\n"
                }
            },
            "Type": "AWS::AutoScaling::LaunchConfiguration"
        }
    }
}

GOOD_CF_DEFINITION_WITH_UNUSUAL_AUTOSCALING_RESOURCE = {
    "AWSTemplateFormatVersion": "2010-09-09",
    "Mappings": {
        "Senza": {
            "Info": {
                "StackName": "abc",
                "StackVersion": "2"
            }
        }
    },
    "Parameters": {},
    "Resources": {
        "NiceClusterConfig": {
            "Properties": {
                "ImageId": "image-id",
                "InstanceType": "t2.micro",
                "UserData": {
                    "Fn::Base64": "#taupage-config\napplication_id: abc\nsource: pierone.example.com/lizzy/lizzy:12\n"
                }
            },
            "Type": "AWS::AutoScaling::LaunchConfiguration"
        }
    }
}

BAD_CF_MISSING_TAUPAGE_AUTOSCALING_GROUP = {
    "AWSTemplateFormatVersion": "2010-09-09",
    "Mappings": {
        "Senza": {
            "Info": {
                "StackName": "abc",
                "StackVersion": "2"
            }
        }
    },
    "Parameters": {},
    "Resources": {
        "AppServerConfig": {
            "Properties": {
                "ImageId": "image-id",
                "InstanceType": "t2.micro",
                "UserData": {}
            },
            "Type": "AWS::Else"
        }
    }
}

BAD_CF_DEFINITION = {
    "AWSTemplateFormatVersion": "2010-09-09",
    "Mappings": {
        "Senza": {
            "Info": {
                "StackName": "abc",
                "StackVersion": "2"
            }
        }
    },
    "Parameters": {},
    "Resources": {
        "AppServerConfig": {
            "Properties": {
                "ImageId": "image-id",
                "InstanceType": "t2.micro",
                "UserData": {}
            },
            "Type": "AWS::AutoScaling::LaunchConfiguration"
        }
    }
}
