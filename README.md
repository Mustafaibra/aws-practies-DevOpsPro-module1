Automating a Serverless CI/CD Pipeline with AWS Developer Tools


**Objective:** To build a fully automated CI/CD pipeline that automatically builds, tests, and deploys a serverless application (an AWS Lambda function behind an API Gateway) whenever code is committed to a source repository.


1- get the lambda code and add it to the handler 

```
import json

  

def lambda_handler(event,context):

    name = event.get('name' , 'World')

    greeting = f"Hello , {name}!"

    return {

        'statusCode' : 200,

        'body' : json.dumps(greeting)

    }

  
  

# if __name__ == "__main__":

#     print(lambda_handler({"name": "Mustafa"}, None))

#     print(lambda_handler({}, None))
```

2- create test for ur funtion 

```
import lambda_function

  

event ={'name' : 'Lab User'}

context = {}

  
  

response = lambda_function.lambda_handler(event, context)

  

print("test response:" , response)

assert "Lab User" in response['body'], "Unit Test Failed: Name not found in response"

print("Unit Test Passed!")
```


3- create the buildspec on the same repo 
```
version: 0.2

  

phases:

  install:

    runtime-versions:

      python: 3.8

  pre_build:

    commands:

      - pip install -r requirements.txt

  build:

    commands:

      - python test_lambda.py

  post_build:

    commands:

      - zip -r deployment.zip lambda_function.py

  

artifacts:

  files:

    - lambda_function.py
```

4- create the project in codebuild to genertae the artifatact 
*cretae service role to add it to cb project , to handle lambda and s3 only *
```
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:GetBucketLocation",
        "s3:ListBucket"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "lambda:UpdateFunctionCode",
        "lambda:GetFunction",
        "lambda:PublishVersion"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "*"
    }
  ]
}

```

5- add this part enhance time in ur buildspec.yml will not work probably with python but can be useful in another cases
```
cache:

  paths:

    - /root/.cache/pip/**/*

    - /root/.pyenv/**/*

```


infra thing 

1-sam deploy   --template-file template.yml   --stack-name my-lambda-infra-stack   --capabilities CAPABILITY_NAMED_IAM   --region eu-north-1 --s3-bucket cicd-dev-mustafa

infra templete
```
AWSTemplateFormatVersion: '2010-09-09'

Transform: AWS::Serverless-2016-10-31

  

Resources:

  # The Lambda Function

  MyHelloWorldFunction:

    Type: AWS::Serverless::Function

    Properties:

      Handler: lambda_function.lambda_handler

      Runtime: python3.8

      CodeUri: ./deployment.zip  # Use a dummy placeholder

      AutoPublishAlias: live      # SAM creates and manages the 'live' alias

  

  # CodeDeploy Application - Manages deployments for this app

  MyCodeDeployApplication:

    Type: AWS::CodeDeploy::Application

    Properties:

      ComputePlatform: Lambda

  

  # CodeDeploy Deployment Group - Defines HOW to deploy

  MyCodeDeployDeploymentGroup:

    Type: AWS::CodeDeploy::DeploymentGroup

    Properties:

      ApplicationName: !Ref MyCodeDeployApplication

      ServiceRoleArn: arn:aws:iam::686255975873:role/codedeploy # You need to create this role

      DeploymentConfigName: CodeDeployDefault.LambdaCanary10Percent5Minutes

      DeploymentStyle:

        DeploymentType: BLUE_GREEN

        DeploymentOption: WITH_TRAFFIC_CONTROL

  

  # # IAM Role for CodeDeploy

  # CodeDeployServiceRole:

  #   Type: AWS::IAM::Role

  #   Properties:

  #     AssumeRolePolicyDocument:

  #       Version: '2012-10-17'

  #       Statement:

  #         - Effect: Allow

  #           Principal:

  #             Service: codedeploy.amazonaws.com

  #           Action: sts:AssumeRole

  #     ManagedPolicyArns:

  #       - arn:aws:iam::aws:policy/service-role/AWSCodeDeployRoleForLambda

  

Outputs:

  FunctionName:

    Description: "Lambda Function Name"

    Value: !Ref MyHelloWorldFunction

  CodeDeployApp:

    Description: "CodeDeploy Application Name"

    Value: !Ref MyCodeDeployApplication

  CodeDeployDeploymentGroup:

    Description: "CodeDeploy Deployment Group Name"

    Value: !Ref MyCodeDeployDeploymentGroup
```
add this to codepipline to call code deploy 
```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "codedeploy:CreateDeployment",
                "codedeploy:GetDeployment",
                "codedeploy:GetDeploymentConfig"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "codedeploy:GetApplicationRevision",
                "codedeploy:RegisterApplicationRevision"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "lambda:UpdateAlias"
            ],
            "Resource": "*"
        }
    ]
}
```


you should have both versions of lambda , inside ur AWS , to use code deploy successfully so 

- buildspec.yml
phases:
  build:
    commands:
      - aws lambda update-function-code --function-name MyFunction --zip-file fileb://function.zip
      - VERSION=$(aws lambda publish-version --function-name MyFunction --query Version --output text)
      - echo "Version: $VERSION"
      - echo "{\"Resources\":[{\"myLambdaFunction\":{\"Type\":\"AWS::Lambda::Function\",\"Properties\":{\"Name\":\"MyFunction\",\"Alias\":\"prod\",\"CurrentVersion\":\"$CODEDEPLOY_CURRENT_VERSION\",\"TargetVersion\":\"$VERSION\"}}}]}" > appspec.json

or 
version: 0.0
Resources:
  - myLambdaFunction:
      Type: AWS::Lambda::Function
      Properties:
        Name: "MyFunction"
        Alias: "prod"
        CurrentVersion: "5"
        TargetVersion: "$LATEST"
