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
