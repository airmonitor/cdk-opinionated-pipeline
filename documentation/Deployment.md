# Deployment Guide

## Deployment Architecture

## Prerequisites

### Required Tools

| Tool        | Version     | Purpose                           | Installation                                                                                          |
| ----------- | ----------- | --------------------------------- | ----------------------------------------------------------------------------------------------------- |
| Python      | 3.13+       | Core programming language         | [python.org](https://www.python.org/downloads/)                                                       |
| AWS CDK CLI | v2 (2.0.0+) | Infrastructure as Code deployment | `npm install -g aws-cdk`                                                                              |
| AWS CLI     | v2          | AWS resource management           | [AWS CLI Installation](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) |
| Docker      | Latest      | Container management and testing  | [docker.com](https://docs.docker.com/get-docker/)                                                     |
| Make        | Latest      | Workflow automation               | Included in most Unix systems                                                                         |
| Git         | Latest      | Source code management            | [git-scm.com](https://git-scm.com/downloads)                                                          |

### AWS Account Requirements

### Required IAM Permissions

## Environment Setup

### Local Development Environment

## Environment Setup

### Local Development Environment

1. Clone the repository:

   ```shell
   git clone repo name
   cd repo name
   ```

2. Create and activate a Python virtual environment:

   ```shell
   # Create virtual environment
   make venv

   # Activate virtual environment (Linux/macOS)
   . .venv/bin/activate

   # Activate virtual environment (Windows)
   .venv\Scripts\activate.bat
   ```

3. Install dependencies:

   ```shell
   make install
   ```

4. Install pre-commit hooks:

   ```shell
   make pre-commit
   ```

### AWS Credentials Configuration

Configure AWS credentials for each environment:

```shell
# For DEV environment
aws configure --profile dev
export AWS_PROFILE=dev

# For ACC environment
aws configure --profile acc
export AWS_PROFILE=acc

# For PROD environment
aws configure --profile prod
export AWS_PROFILE=prod
```

### Required IAM Permissions

To successfully deploy the infrastructure, your AWS credentials should have the following permissions:

- CloudFormation: Full access to create, update, and delete stacks
- IAM: Create roles, policies, and instance profiles
- S3: Create buckets and manage objects
- ECR: Create repositories and manage images
- CodeBuild: Create and manage build projects
- CodePipeline: Create and manage pipelines
- SSM: Create and manage parameters
- SNS: Create topics and manage subscriptions
- CloudWatch: Create dashboards, alarms, and log groups
- AWS Signer: Create signing profiles

For development purposes, the `PowerUser` policy can be used, but for production,
a more restricted policy following the principle of least privilege should be created.

## Configuration

The infrastructure uses a hierarchical configuration approach with environment-specific settings and global CI/CD
configuration. This section explains how to configure the infrastructure for deployment.

### Configuration Structure

The configuration is organized in the following structure:

```
cdk/
├── config/
│   ├── config-ci-cd.yaml       # Global CI/CD configuration
│   ├── dev/
│   │   └── config.yaml         # Development environment configuration
```

### Core Configuration Files

| Configuration File             | Purpose                             | Required Changes                                      |
| ------------------------------ | ----------------------------------- | ----------------------------------------------------- |
| `cdk/config/config-ci-cd.yaml` | Global CI/CD pipeline configuration | AWS accounts, regions, repository info, notifications |
| `cdk/config/dev/config.yaml`   | Development environment settings    | Resource sizing, feature flags, budget limits         |

### Global CI/CD Configuration Parameters

The `config-ci-cd.yaml` file contains global settings for the CI/CD pipeline:

| Parameter                  | Description                           | Example Value                   |
| -------------------------- | ------------------------------------- | ------------------------------- |
| `project`                  | Project name used for resource naming | \`\`                            |
| `aws_account`              | CI/CD account ID                      | \`\`                            |
| `aws_region`               | Primary AWS region                    | \`\`                            |
| `aws_dev_account`          | Development account ID                | \`\`                            |
| `aws_dev_region`           | Development region                    | \`\`                            |
| `git_repo`                 | Git repository name                   | \`\`                            |
| `git_connection_arn`       | AWS CodeStar connection ARN           | `"arn:aws:codeconnections:..."` |
| `ci_cd_notification_email` | Notification email address            | `"team@example.com"`            |
| `tags`                     | Resource tags                         | See example below               |

### Environment-Specific Configuration Parameters

Each environment-specific `config.yaml` file contains settings for that environment:

| Parameter          | Description                       | Example Value |
| ------------------ | --------------------------------- | ------------- |
| `stage`            | Environment name (dev, acc, prod) | `"dev"`       |
| `project`          | Project name                      | \`\`          |
| `aws_account`      | Environment account ID            | `""`          |
| `aws_region`       | Environment region                | `""`          |
| `budget_limit`     | Monthly budget limit in USD       | \`\`          |
| `budget_threshold` | Budget alert threshold percentage | \`\`          |

### Configuration Example

Here's an example of the `config-ci-cd.yaml` file:

## Deployment Process

This section provides a step-by-step guide for deploying the infrastructure across all environments.
The deployment follows a progressive model, starting with the CI/CD pipeline and then deploying to development,
acceptance, and production environments.

### Deployment Workflow Overview

The deployment process follows these high-level steps:

1. **Bootstrap AWS Environments**: Prepare AWS accounts for CDK deployments
2. **Configure the Infrastructure**: Update configuration files for each environment
3. **Validate Configuration**: Run tests to verify configuration correctness
4. **Deploy Pipeline Stack**: Deploy the CI/CD pipeline to the pipeline account
5. **Monitor Pipeline Execution**: The pipeline automatically deploys to all environments
6. **Verify Deployment**: Confirm all resources are created correctly

### 1. Initial Bootstrap

Before deploying any stacks, you must bootstrap the AWS CDK in each environment. This creates the necessary resources
for CDK deployments.

#### Bootstrap Commands

```shell
# Bootstrap CI/CD environment
export AWS_PROFILE=cicd
cdk bootstrap aws://CI_CD_AWS_ACCOUNT_NUMBER/eu-central-1

# Bootstrap DEV environment
export AWS_PROFILE=konnect-dev
cdk bootstrap aws://AWS_DEV_ACCOUNT/eu-central-1 --trust CI_CD_AWS_ACCOUNT_NUMBER --trust-for-lookup CI_CD_AWS_ACCOUNT_NUMBER
```

#### Bootstrap Resources Created

The bootstrap process creates the following resources in each account:

| Resource       | Purpose                                           |
| -------------- | ------------------------------------------------- |
| S3 Bucket      | Stores CloudFormation templates and assets        |
| IAM Roles      | Provides permissions for CloudFormation execution |
| ECR Repository | Stores Docker images for CDK assets               |
| SSM Parameters | Stores bootstrap configuration                    |

#### Verifying Bootstrap Success

To verify successful bootstrapping, check for the CDK toolkit stack in each account:

```shell
aws cloudformation describe-stacks --stack-name CDKToolkit --query "Stacks[0].StackStatus" --output text
```

The output should be `CREATE_COMPLETE` or `UPDATE_COMPLETE`.

### 2. Deployment Preparation

Before deploying, prepare your local environment and validate the configuration.

#### Set Up Local Environment

```shell
# Clone the repository
git clone repo name
cd repo name

# Create and activate virtual environment
make venv
. .venv/bin/activate

# Install dependencies
make install

# Install pre-commit hooks
make pre-commit

# Update tests
for i in dev; do STAGE=$i make update-tests; done
```

#### Validate Configuration

```shell
# Run infrastructure tests
for i in dev; do STAGE=$i make tests; done
```

The tests verify:

- All required configuration parameters are present
- Stack resources are created as expected
- IAM permissions follow the principle of least privilege
- Security best practices are followed

#### Synthesize CloudFormation Templates

Generate CloudFormation templates for review:

```shell
# List all stacks
cdk ls

# Synthesize templates
cdk synth -q

# Review differences (if updating existing deployment)
cdk diff
```

### 3. Deploy the Pipeline Stack

The pipeline stack is the entry point for all deployments. It creates the CI/CD pipeline that deploys all other stacks.

#### Pipeline Deployment Command

```shell
# Set AWS profile for CI/CD account
export AWS_PROFILE=cicd

# Deploy the pipeline stack
cdk deploy pipeline stack name
```

#### Pipeline Stack Resources

The pipeline stack creates the following resources:

| Resource           | Purpose                                     |
| ------------------ | ------------------------------------------- |
| CodePipeline       | Orchestrates the CI/CD workflow             |
| CodeBuild Projects | Execute build and deployment tasks          |
| S3 Bucket          | Stores pipeline artifacts                   |
| IAM Roles          | Provides permissions for pipeline execution |
| SNS Topics         | Sends notifications for pipeline events     |

### 4. Monitor Pipeline Execution

After deploying the pipeline stack, the CI/CD pipeline automatically deploys the remaining stacks in the following
order:

#### Pipeline Stages

| Stage                  | Purpose                                  | Resources Created    |
| ---------------------- | ---------------------------------------- | -------------------- |
| Source                 | Retrieves code from Git repository       | None                 |
| Artefact               | Creates SSM parameters for configuration | SSM Parameters       |
| Code Quality           | Runs code quality checks                 | None                 |
| Infrastructure Tests   | Tests infrastructure code                | None                 |
| Plugins (Dev)          | Deploys environment-specific plugins     | Various              |
| Shared Resources (Dev) | Deploys shared infrastructure            | IAM, S3, ECR, Signer |
| Docker (Dev)           | Builds and deploys Docker images         | Docker Images        |

#### Monitoring Pipeline Progress

You can monitor the pipeline execution in the AWS CodePipeline console:

```
https://eu-central-1.console.aws.amazon.com/codesuite/codepipeline/pipelines?region=eu-central-1
```

Or using the AWS CLI:

```shell
aws codepipeline get-pipeline-state --name pipeline name
```

### 5. Deployment Verification

After deployment completes, verify that all resources were created correctly in each environment.

#### Verification Checklist

| Resource              | Verification Method | Expected State                         |
| --------------------- | ------------------- | -------------------------------------- |
| CloudFormation Stacks | AWS Console or CLI  | `CREATE_COMPLETE` or `UPDATE_COMPLETE` |
| ECR Repositories      | AWS Console or CLI  | Contains tagged images                 |
| S3 Buckets            | AWS Console or CLI  | Created with correct policies          |
| IAM Roles             | AWS Console or CLI  | Created with correct permissions       |
| AWS Signer Profiles   | AWS Console or CLI  | Created and active                     |
| SSM Parameters        | AWS Console or CLI  | Contains correct values                |

#### Verification Commands

```shell
# Check CloudFormation stacks
aws cloudformation list-stacks --query "StackSummaries[?StackStatus!='DELETE_COMPLETE']"

# Check ECR repositories
aws ecr describe-repositories --repository-names project-name-${STAGE}

# Check ECR images
aws ecr list-images --repository-name project-name-${STAGE}

# Check S3 buckets
aws s3 ls s3://project-name-${STAGE}

# Check SSM parameters
aws ssm get-parameters-by-path --path "/project-name/${STAGE}" --recursive
```

### 6. Post-Deployment Tasks

After successful deployment, perform these additional tasks:

1. **Update Documentation**: Document any configuration changes or customizations
2. **Notify Stakeholders**: Inform relevant teams about the deployment
3. **Monitor Metrics**: Set up monitoring for the deployed resources
4. **Schedule Regular Reviews**: Plan periodic reviews of the infrastructure

## Security Considerations

### IAM Permissions

Ensure that your AWS credentials have the necessary permissions to:

- Create and manage IAM roles and policies
- Create and manage CloudFormation stacks
- Access ECR repositories
- Create and manage S3 buckets
- Create and manage CodePipeline resources

### Secrets Management

- Do not store sensitive information in configuration files
- Use AWS Secrets Manager or SSM Parameter Store for sensitive values
- Ensure that IAM roles follow the principle of least privilege
- Rotate access keys regularly (every 90 days)
- Use temporary credentials when possible

### Deployment Validation

Always validate deployments before proceeding to production:

1. Run infrastructure tests: `make tests`
2. Review CloudFormation change sets: `cdk diff`
3. Verify resources in the AWS Console after deployment
4. Check for security vulnerabilities in Docker images
5. Validate image signatures

### Security Checklist

Before deploying to production, ensure:

- [ ] All IAM roles follow the principle of least privilege
- [ ] IAM policies use specific resources and conditions where possible
- [ ] S3 buckets have appropriate access controls and encryption
- [ ] S3 buckets have public access blocked
- [ ] ECR repositories have image scanning enabled
- [ ] Docker images are scanned for vulnerabilities with no critical findings
- [ ] Docker images are signed and validated
- [ ] No secrets are stored in code, configuration files, or environment variables
- [ ] All sensitive data is encrypted at rest and in transit
- [ ] CloudTrail logging is enabled with log file validation
- [ ] CloudWatch alarms are configured for security events
- [ ] VPC Flow Logs are enabled for network monitoring
- [ ] MFA is enabled for AWS console access
- [ ] Security groups follow the principle of least privilege
- [ ] Regular security assessments are scheduled
- [ ] Automated security testing is integrated into the CI/CD pipeline
- [ ] Security incident response plan is documented and tested

## Operational Procedures

### Updating the Infrastructure

To update the infrastructure:

1. Make changes to the CDK code
2. Run tests: `make tests`
3. Update test snapshots if needed: `make update-tests`
4. Commit and push changes
5. The CI/CD pipeline will automatically deploy the changes

For critical updates that need to be deployed immediately:

```shell
# Deploy a specific stack
export STAGE=dev
export AWS_PROFILE=dev
cdk deploy STACK_NAME
```

### Support Resources

- AWS CDK Documentation: https://docs.aws.amazon.com/cdk/
- AWS CloudFormation Documentation: https://docs.aws.amazon.com/cloudformation/
- AWS CodePipeline Documentation: https://docs.aws.amazon.com/codepipeline/
- AWS ECR Documentation: https://docs.aws.amazon.com/ecr/
- Team MS Teams
  Channel: [link](https://teams.microsoft.com/l/channel/19%3Abc62bcf1085d41b0b25ad6ab321cff18%40thread.tacv2/General?groupId=6f4ba405-9310-48e2-9604-bd7aec766262&tenantId=7b775fdb-ccca-4138-8f0f-4acc5785f9f2)

## Useful Commands

### CDK Commands

- `cdk ls` - List all stacks in the app
- `cdk synth -q` - Synthesize CloudFormation templates
- `cdk deploy [stack-name]` - Deploy stack to AWS
- `cdk diff` - Compare deployed stack with current state
- `cdk destroy [stack-name]` - Delete a stack

### Makefile Commands

- `make help` - Display available commands
- `make venv` - Create Python virtual environment
- `make install` - Install dependencies
- `make pre-commit` - Run code quality checks
- `make tests` - Run infrastructure tests
- `make update-tests` - Update test snapshots
- `make diagrams` - Generate architecture diagrams
- `make clean` - Remove virtual environment and cleanup
