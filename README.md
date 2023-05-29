## Use case

## Stories

## Requirements

### Flows

### Functional

### Non-functional

## Architecture

### Architectural Decision Record 1 - Application

#### Context

We need to create application architecture to address the requirements. The architecture should define component
boundaries and integration patterns between them.

#### Decision

#### Consequences

### Architectural Decision Record 2 - Flows

#### Context

We need to define flows between the application components.

#### Decision

#### Consequences

### Architectural Decision Record 3 - Title

#### Context

#### Decision

#### Consequences

## Implementation

### Toolchain

### Git repositories

### Project structure

## Backlog

# Prerequisites

For above please use script tools/create_ssm_parameters.py

* Secret for GitHub access token in Secrets Manager
  * sonyhive_ci_cd_pipeline_github_access_token

For above please use script tools/create_secret_manager_secret.py

To manually create a virtualenv on MacOS and Linux:

```
$ python3 -m venv .venv
```

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

```
$ source .venv/bin/activate
```

If you are a Windows platform, you would activate the virtualenv like this:

```
% .venv\Scripts\activate.bat
```

Once the virtualenv is activated, you can install the required dependencies.

```
$ pip install -r requirements.txt
```

At this point you can now synthesize the CloudFormation template for this code.

```
$ cdk synth
```

To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

## Useful commands

* `cdk ls`          list all stacks in the app
* `cdk synth`       emits the synthesized CloudFormation template
* `cdk deploy`      deploy this stack to your default AWS account/region
* `cdk diff`        compare deployed stack with current state
* `cdk docs`        open CDK documentation

Enjoy!

# Documentation

The code documentation was created automatically by pydoctor using following command:

```shell
  pydoctor --docformat restructuredtext --make-html --html-output=docs/ci_cd sonyhive_ci_cd_pipeline
```

Documentation is placed in docs/ci_cd/index.html directory.

**Please remember to update documentation using above command.**
