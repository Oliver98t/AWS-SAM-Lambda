# sam-app

An event-driven serverless pipeline built with AWS SAM and container-based Lambda functions.

## Architecture

```
HTTP GET /hello
    │
    ▼
Function1 (Lambda)
    │  publishes message {"value": 400}
    ▼
SQS Queue
    │  triggers
    ▼
Function2 (Lambda)
    │  writes item
    ▼
DynamoDB Table
```

| Resource | Type | Purpose |
|---|---|---|
| `Function1` | Lambda (container) | Receives HTTP request, sends message to SQS |
| `Function2` | Lambda (container) | Consumes SQS message, writes to DynamoDB |
| `SQSQueue1` | SQS Queue | Decouples Function1 from Function2 |
| `Table` | DynamoDB | Stores processed records |

## CI/CD — GitHub Actions

Deployments to AWS are automated via `.github/workflows/cd.yaml` on every push to `main`. It uses OIDC (no stored AWS access keys).

### One-time AWS setup

**1. Create the GitHub OIDC provider** (only needed once per AWS account):
```bash
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1 \
  --region eu-west-2
```

**2. Create the IAM role with a trust policy** that authorises this repository:
```bash
cat > trust-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::<ACCOUNT_ID>:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:Oliver98t/AWS-SAM-Lambda:*"
        }
      }
    }
  ]
}
EOF

aws iam create-role \
  --role-name GitHubActions-sam-app \
  --assume-role-policy-document file://trust-policy.json

aws iam attach-role-policy \
  --role-name GitHubActions-sam-app \
  --policy-arn arn:aws:iam::aws:policy/AdministratorAccess
```

**3. Get the role ARN:**
```bash
aws iam get-role --role-name GitHubActions-sam-app \
  --query "Role.Arn" --output text
```

**4. Add the role ARN as a GitHub secret:**

Go to **GitHub repo → Settings → Secrets and variables → Actions** and create:

| Secret name | Value |
|---|---|
| `AWS_ROLE_ARN` | `arn:aws:iam::<ACCOUNT_ID>:role/GitHubActions-sam-app` |

### Verify the setup

```bash
# Confirm trust policy has the correct repo name
aws iam get-role --role-name GitHubActions-sam-app \
  --query "Role.AssumeRolePolicyDocument" --output json

# Confirm OIDC provider exists
aws iam list-open-id-connect-providers --output json
```

Once the secret is set, push to `main` and the workflow will build and deploy automatically.

---

## Prerequisites

- [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html)
- [Docker](https://hub.docker.com/search/?type=edition&offering=community)
- AWS credentials configured (`~/.aws/credentials`)

## Deploy

First-time setup (saves config to `samconfig.toml`):

```bash
sam build
sam deploy --guided
```

Subsequent deployments:

```bash
sam build && sam deploy
```

## Local Development

### Run Function1 as a live HTTP endpoint

```bash
sam local start-api
curl http://localhost:3000/hello
```

### Invoke functions directly with test events

```bash
# Function1 (HTTP trigger)
sam local invoke Function1 --event events/Function1Event.json

# Function2 (SQS trigger)
sam local invoke Function2 --event events/Function2Event.json --env-vars events/env.json
```

> `events/env.json` is required for local invocation of Function2 because CloudFormation intrinsic functions (`!Ref`, `!GetAtt`) don't resolve locally. Generate it with:
> ```bash
> TABLE_NAME=$(aws cloudformation describe-stack-resource --stack-name sam-container --logical-resource-id Table --query "StackResourceDetail.PhysicalResourceId" --output text --region eu-west-2)
> QUEUE_URL=$(aws cloudformation describe-stack-resource --stack-name sam-container --logical-resource-id SQSQueue1 --query "StackResourceDetail.PhysicalResourceId" --output text --region eu-west-2)
> echo "{\"Function1\":{\"SQSQUEUE1_QUEUE_URL\":\"$QUEUE_URL\"},\"Function2\":{\"TABLE_TABLE_NAME\":\"$TABLE_NAME\"}}" > events/env.json
> ```

### Watch mode (syncs changes to AWS automatically)

```bash
sam sync --stack-name sam-container
```

## Tests

```bash
pip install -r tests/requirements.txt
pytest tests/unit -v
```

## Logs

```bash
sam logs --stack-name sam-container --tail
```

## Cleanup

```bash
aws cloudformation delete-stack --stack-name sam-container --region eu-west-2
```

If you prefer to use an integrated development environment (IDE) to build and test your application, you can use the AWS Toolkit.  
The AWS Toolkit is an open source plug-in for popular IDEs that uses the SAM CLI to build and deploy serverless applications on AWS. The AWS Toolkit also adds a simplified step-through debugging experience for Lambda function code. See the following links to get started.

* [CLion](https://docs.aws.amazon.com/toolkit-for-jetbrains/latest/userguide/welcome.html)
* [GoLand](https://docs.aws.amazon.com/toolkit-for-jetbrains/latest/userguide/welcome.html)
* [IntelliJ](https://docs.aws.amazon.com/toolkit-for-jetbrains/latest/userguide/welcome.html)
* [WebStorm](https://docs.aws.amazon.com/toolkit-for-jetbrains/latest/userguide/welcome.html)
* [Rider](https://docs.aws.amazon.com/toolkit-for-jetbrains/latest/userguide/welcome.html)
* [PhpStorm](https://docs.aws.amazon.com/toolkit-for-jetbrains/latest/userguide/welcome.html)
* [PyCharm](https://docs.aws.amazon.com/toolkit-for-jetbrains/latest/userguide/welcome.html)
* [RubyMine](https://docs.aws.amazon.com/toolkit-for-jetbrains/latest/userguide/welcome.html)
* [DataGrip](https://docs.aws.amazon.com/toolkit-for-jetbrains/latest/userguide/welcome.html)
* [VS Code](https://docs.aws.amazon.com/toolkit-for-vscode/latest/userguide/welcome.html)
* [Visual Studio](https://docs.aws.amazon.com/toolkit-for-visual-studio/latest/user-guide/welcome.html)

## Deploy the sample application

The Serverless Application Model Command Line Interface (SAM CLI) is an extension of the AWS CLI that adds functionality for building and testing Lambda applications. It uses Docker to run your functions in an Amazon Linux environment that matches Lambda. It can also emulate your application's build environment and API.

To use the SAM CLI, you need the following tools.

* SAM CLI - [Install the SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html)
* [Python 3 installed](https://www.python.org/downloads/)
* Docker - [Install Docker community edition](https://hub.docker.com/search/?type=edition&offering=community)

To build and deploy your application for the first time, run the following in your shell:

```bash
sam build --use-container
sam deploy --guided
```

The first command will build the source of your application. The second command will package and deploy your application to AWS, with a series of prompts:

* **Stack Name**: The name of the stack to deploy to CloudFormation. This should be unique to your account and region, and a good starting point would be something matching your project name.
* **AWS Region**: The AWS region you want to deploy your app to.
* **Confirm changes before deploy**: If set to yes, any change sets will be shown to you before execution for manual review. If set to no, the AWS SAM CLI will automatically deploy application changes.
* **Allow SAM CLI IAM role creation**: Many AWS SAM templates, including this example, create AWS IAM roles required for the AWS Lambda function(s) included to access AWS services. By default, these are scoped down to minimum required permissions. To deploy an AWS CloudFormation stack which creates or modifies IAM roles, the `CAPABILITY_IAM` value for `capabilities` must be provided. If permission isn't provided through this prompt, to deploy this example you must explicitly pass `--capabilities CAPABILITY_IAM` to the `sam deploy` command.
* **Save arguments to samconfig.toml**: If set to yes, your choices will be saved to a configuration file inside the project, so that in the future you can just re-run `sam deploy` without parameters to deploy changes to your application.

You can find your API Gateway Endpoint URL in the output values displayed after deployment.

## Use the SAM CLI to build and test locally

Build your application with the `sam build --use-container` command.

```bash
sam-app$ sam build --use-container
```

The SAM CLI installs dependencies defined in `hello_world/requirements.txt`, creates a deployment package, and saves it in the `.aws-sam/build` folder.

Test a single function by invoking it directly with a test event. An event is a JSON document that represents the input that the function receives from the event source. Test events are included in the `events` folder in this project.

Run functions locally and invoke them with the `sam local invoke` command.

```bash
sam-app$ sam local invoke HelloWorldFunction --event events/event.json
```

The SAM CLI can also emulate your application's API. Use the `sam local start-api` to run the API locally on port 3000.

```bash
sam-app$ sam local start-api
sam-app$ curl http://localhost:3000/
```

The SAM CLI reads the application template to determine the API's routes and the functions that they invoke. The `Events` property on each function's definition includes the route and method for each path.

```yaml
      Events:
        HelloWorld:
          Type: Api
          Properties:
            Path: /hello
            Method: get
```

## Add a resource to your application
The application template uses AWS Serverless Application Model (AWS SAM) to define application resources. AWS SAM is an extension of AWS CloudFormation with a simpler syntax for configuring common serverless application resources such as functions, triggers, and APIs. For resources not included in [the SAM specification](https://github.com/awslabs/serverless-application-model/blob/master/versions/2016-10-31.md), you can use standard [AWS CloudFormation](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-template-resource-type-ref.html) resource types.

## Fetch, tail, and filter Lambda function logs

To simplify troubleshooting, SAM CLI has a command called `sam logs`. `sam logs` lets you fetch logs generated by your deployed Lambda function from the command line. In addition to printing the logs on the terminal, this command has several nifty features to help you quickly find the bug.

`NOTE`: This command works for all AWS Lambda functions; not just the ones you deploy using SAM.

```bash
sam-app$ sam logs -n HelloWorldFunction --stack-name "sam-app" --tail
```

You can find more information and examples about filtering Lambda function logs in the [SAM CLI Documentation](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-logging.html).

## Tests

Tests are defined in the `tests` folder in this project. Use PIP to install the test dependencies and run tests.

```bash
sam-app$ pip install -r tests/requirements.txt --user
# unit test
sam-app$ python -m pytest tests/unit -v
# integration test, requiring deploying the stack first.
# Create the env variable AWS_SAM_STACK_NAME with the name of the stack we are testing
sam-app$ AWS_SAM_STACK_NAME="sam-app" python -m pytest tests/integration -v
```

## Cleanup

To delete the sample application that you created, use the AWS CLI. Assuming you used your project name for the stack name, you can run the following:

```bash
sam delete --stack-name "sam-app"
```

## Resources

See the [AWS SAM developer guide](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/what-is-sam.html) for an introduction to SAM specification, the SAM CLI, and serverless application concepts.

Next, you can use AWS Serverless Application Repository to deploy ready to use Apps that go beyond hello world samples and learn how authors developed their applications: [AWS Serverless Application Repository main page](https://aws.amazon.com/serverless/serverlessrepo/)
