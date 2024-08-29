
## Deployment

## Prerequisites

* Python 3.11
* AWS CDK CLI
* AWS account and configured credentials
* Ability to execute Makefiles

## Setup

1. Clone the repository:

   ```shell
   git clone ....

2. To manually create a virtualenv on macOS and Linux:

```shell
make venv
```

3. After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

```shell
source .venv/bin/activate
```

If you are a Windows platform, you would activate the virtualenv like this:

```shell
% .venv\Scripts\activate.bat
```

4. Once the virtualenv is activated, you can install the required dependencies.

```shell
make local_install
```

## Configuration

Update the cdk/config/config-ci-cd.yaml file with your specific AWS account details, GitHub repository information, and other required parameters.

Ensure your AWS credentials are properly configured for the target account and region.

## Deployment

1. Synthesize the CloudFormation template:

```shell
cdk synth
```

2. Review the generated CloudFormation template in the cdk.out directory.

Deploy the stack:

```shell
cdk deploy
```


## Useful commands

* `make help`       lists all available commands from Makefile
* `cdk ls`          list all stacks in the app
* `cdk synth`       emits the synthesized CloudFormation template
* `cdk deploy`      deploy this stack to your default AWS account/region
* `cdk diff`        compare deployed stack with current state
* `cdk docs`        open CDK documentation
